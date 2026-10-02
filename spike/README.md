# Branch `spike/step7`: unmerged Step 7 spike

> **INDICATIVE ONLY. Unmerged, throwaway work.** Nothing under `spike/` is a project result.
> Every file under `spike/` is indicative only, including the files that carry no label of
> their own: the two Task 3 CSVs, `out/task3_summary.json` and `task1_samples.json`.

- **What it is.** A spike that asked whether the Step 7 idea (ranking a candidate set on two
  standardized axes) has a blocker, using a throwaway title-keyword matcher. The matcher is
  known to be defective on one of its five queries and to admit accessories and other
  products into its candidate sets.
- **Findings and corrections log:** [`FINDINGS.md`](FINDINGS.md).
- **What the project kept:** questions and mechanisms, recorded on `main` in
  CONSIDERATIONS.md §11, a section headed and introduced as indicative. `FINDINGS.md` says no
  spike figure may enter CONSIDERATIONS.md; `main` later admitted figures labelled
  indicative into §11, as a deliberate exception (§10 also quotes the corrected figures behind
  the agent's spike overclaims), and bars them from README.md, SPEC.md and the portfolio page
  until re-measured. DECISIONS.md carries pointers, not figures.
- **Files outside `spike/`** are a snapshot of `main` at commit `809576b`, when this branch
  was created, and are superseded by `main`. They include the project's Step 2–5 results as
  they stood then. This branch's CONSIDERATIONS.md §10 still states a human-to-agent ratio
  that `main` later removed (`2ef9b24`), and it has no §11. The root README.md is likewise
  `main`'s, as it was at `809576b`.
- **Reproducing.** The scripts read `data/raw/meta_Health_and_Household.slim.parquet`,
  which `make data` builds on `main`. `task4_checks.py` reproduces the two follow-up
  sections of `out/task4.json`; run it after `task4.py`, which rewrites that file without
  them. Some figures in `FINDINGS.md` rest on console output and on the agent's per-item
  reading during the spike, not on committed files: for example the toilet-paper extraction
  examples, the grab-bar reading, the `Item Weight` counts and the tail-error splits.
- **Data.** Product IDs, titles, prices and ratings in `out/` and `task1_samples.json` are
  excerpts of Amazon Reviews 2023 (McAuley Lab, UC San Diego; Hou et al. 2024,
  arXiv:2403.03952), for which no license is granted. See the data notice in README.md on
  `main`. Independent student project, not affiliated with or endorsed by Amazon.
