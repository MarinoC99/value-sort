.PHONY: data build eval demo test

# Each target fails loudly until its step is implemented, so nothing
# pretends to have produced output it hasn't.

data:   ## Step 2: download one category, cache to data/raw/, profile it
	@echo "make data: not implemented yet (Step 2)" && exit 1

build:  ## Steps 3-7: load, score (CAR, unit price, attributes), rank
	@echo "make build: not implemented yet (Steps 3-7)" && exit 1

eval:   ## Step 8: rank displacement + extraction precision -> eval/results.md
	@echo "make eval: not implemented yet (Step 8)" && exit 1

demo:   ## Step 9: static HTML demo
	@echo "make demo: not implemented yet (Step 9)" && exit 1

test:
	uv run pytest -q
