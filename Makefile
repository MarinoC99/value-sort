.PHONY: data load car audit unit-price score-unit-price step7-sample build eval demo test

# Each target fails loudly until its step is implemented, so nothing
# pretends to have produced output it hasn't.

CATEGORY ?= Health_and_Household

# uv marks the editable-install .pth as macOS-hidden and Python 3.11.16 skips hidden
# .pth files, so put src/ on the path explicitly. See DECISIONS.md #11.
export PYTHONPATH := src


data:   ## Step 2: stream one category's metadata to a slim Parquet in data/raw/, then profile it
	uv run python -m value_sort.fetch --category $(CATEGORY)
	uv run python -m value_sort.profile --category $(CATEGORY)

load:   ## Step 3: validate every row into Item records; print drop count and price-null reasons
	uv run python -m value_sort.loader --category $(CATEGORY)
	uv run python -m value_sort.priors --category $(CATEGORY)

car:    ## Step 4: CAR sensitivity over m and C -> reports/car_sensitivity_<Category>.md
	uv run python -m value_sort.car_sensitivity --category $(CATEGORY)

audit:  ## Step 5a: write the 200-item labelling set (refuses to overwrite labels)
	uv run python -m value_sort.unit_price_audit --category $(CATEGORY)

unit-price: ## Step 5b: extractor coverage over the priced pool (no labels needed)
	uv run python -m value_sort.unit_price_score --category $(CATEGORY) --coverage-only

score-unit-price: ## Step 5c: precision against hand labels in audit/unit_price_labels.csv
	uv run python -m value_sort.unit_price_score --category $(CATEGORY)

step7-sample: ## Step 7: draw the blind contamination-audit sample (refuses to overwrite labels)
	uv run python -m value_sort.step7_audit --category $(CATEGORY)

build:  ## Steps 3-7: load, score (CAR, unit price, attributes), rank
	@echo "make build: not implemented yet (Steps 3-7)" && exit 1

eval:   ## Step 8: rank displacement + extraction precision -> eval/results.md
	@echo "make eval: not implemented yet (Step 8)" && exit 1

demo:   ## Step 9: static HTML demo
	@echo "make demo: not implemented yet (Step 9)" && exit 1

test:
	uv run pytest -q
