"""Stream one category's metadata from Hugging Face and keep a slim Parquet copy.

The full JSONL is never written to disk. Bytes are hashed as they stream and checked
against the published sha256, so the slim file is provably derived from the real source.

Only the contract fields are kept. Numeric fields are stored as the raw JSON text of the
source value ("12.99", "null", "\"$5\"") so no coercion happens here; typing and
validation are Step 3's job.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from huggingface_hub import HfApi, HfFileSystem

REPO = "McAuley-Lab/Amazon-Reviews-2023"
CONTRACT_FIELDS = ["parent_asin", "title", "price", "average_rating", "rating_number", "details"]
RAW_TEXT_FIELDS = {"price", "average_rating", "rating_number", "details"}
SCHEMA = pa.schema([(f, pa.string()) for f in CONTRACT_FIELDS])
BATCH_ROWS = 50_000
CHUNK_BYTES = 8 * 1024 * 1024


def meta_path(category: str) -> str:
    return f"raw/meta_categories/meta_{category}.jsonl"


def slim_row(obj: dict) -> dict:
    row = {}
    for f in CONTRACT_FIELDS:
        v = obj.get(f)
        row[f] = json.dumps(v, ensure_ascii=False) if f in RAW_TEXT_FIELDS else v
    return row


def stream_meta(category: str, out_dir: Path) -> dict:
    path = meta_path(category)
    info = HfApi().dataset_info(REPO, files_metadata=True)
    sib = next(s for s in info.siblings if s.rfilename == path)
    expected_sha, expected_size = sib.lfs.sha256, sib.size

    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"meta_{category}.slim.parquet"
    tmp = out.with_suffix(".parquet.partial")

    sha = hashlib.sha256()
    n_bytes = n_rows = 0
    bad_lines: list[tuple[int, str]] = []
    batch: list[dict] = []
    buf = b""
    line_no = 0

    def handle(line: bytes) -> None:
        nonlocal line_no, n_rows
        line_no += 1
        if not line.strip():
            return
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            bad_lines.append((line_no, str(e)))
            return
        batch.append(slim_row(obj))
        n_rows += 1

    fs = HfFileSystem()
    with fs.open(f"datasets/{REPO}/{path}", "rb", block_size=CHUNK_BYTES) as src, \
            pq.ParquetWriter(tmp, SCHEMA, compression="zstd") as writer:
        while chunk := src.read(CHUNK_BYTES):
            sha.update(chunk)
            n_bytes += len(chunk)
            buf += chunk
            *lines, buf = buf.split(b"\n")
            for line in lines:
                handle(line)
            if len(batch) >= BATCH_ROWS:
                writer.write_table(pa.Table.from_pylist(batch, SCHEMA))
                batch.clear()
                print(f"  {n_bytes / 1e6:,.0f} / {expected_size / 1e6:,.0f} MB, {n_rows:,} rows", flush=True)
        handle(buf)
        if batch:
            writer.write_table(pa.Table.from_pylist(batch, SCHEMA))

    if n_bytes != expected_size or sha.hexdigest() != expected_sha:
        tmp.unlink()
        raise RuntimeError(
            f"Integrity check failed: got {n_bytes} bytes sha256={sha.hexdigest()}, "
            f"expected {expected_size} bytes sha256={expected_sha}"
        )
    tmp.rename(out)

    manifest = {
        "source": f"hf://datasets/{REPO}/{path}",
        "source_bytes": expected_size,
        "source_sha256": expected_sha,
        "rows_written": n_rows,
        "unparseable_json_lines": len(bad_lines),
        "unparseable_examples": bad_lines[:20],
        "fields": CONTRACT_FIELDS,
        "output": str(out),
        "output_bytes": out.stat().st_size,
    }
    (out_dir / f"meta_{category}.manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", default="Health_and_Household")
    ap.add_argument("--out-dir", type=Path, default=Path("data/raw"))
    args = ap.parse_args()
    out = args.out_dir / f"meta_{args.category}.slim.parquet"
    if out.exists():
        print(f"{out} exists; skipping download. Delete it to re-stream.")
        return
    m = stream_meta(args.category, args.out_dir)
    print(json.dumps({k: v for k, v in m.items() if k != "unparseable_examples"}, indent=2))


if __name__ == "__main__":
    main()
