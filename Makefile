.PHONY: data build eval demo test

# Each target fails loudly until its step is implemented, so nothing
# pretends to have produced output it hasn't.

CATEGORY ?= Health_and_Household

# uv marks the editable-install .pth as macOS-hidden and Python 3.11.16 skips hidden
# .pth files, so put src/ on the path explicitly. See DECISIONS.md #11.
export PYTHONPATH := src


data:   ## Step 2: stream one category's metadata to a slim Parquet in data/raw/, then profile it
	uv run python -m value_sort.fetch --category $(CATEGORY)
	uv run python -m value_sort.profile --category $(CATEGORY)

build:  ## Steps 3-7: load, score (CAR, unit price, attributes), rank
	@echo "make build: not implemented yet (Steps 3-7)" && exit 1

eval:   ## Step 8: rank displacement + extraction precision -> eval/results.md
	@echo "make eval: not implemented yet (Step 8)" && exit 1

demo:   ## Step 9: static HTML demo
	@echo "make demo: not implemented yet (Step 9)" && exit 1

test:
	uv run pytest -q
