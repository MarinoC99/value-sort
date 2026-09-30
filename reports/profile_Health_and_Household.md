# Profile: Health_and_Household

Source: `data/raw/meta_Health_and_Household.slim.parquet` (slim Parquet streamed from Amazon Reviews 2023).

| Metric | Value |
|---|---|
| Rows (items) | 797,563 |
| Duplicate parent_asin | 0 |
| % items with non-null price | 41.53% |
| % items with numeric price | 41.52% |
| % items with non-null rating_number | 100.0% |
| % items with rating_number >= 1 | 100.0% |
| Category mean rating, C (unweighted, rated items) | 4.1266 |
| Median rating count, m (rated items) | 24 |
| Items in C/m population | 797,563 |

## Price distribution (USD, price > 0)

| n | mean | p1 | p5 | p10 | p25 | p50 | p75 | p90 | p95 | p99 | max |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 331,107 | 33.18 | 4.16 | 6.89 | 8.04 | 11.99 | 19.77 | 32.95 | 57.99 | 85.16 | 208.44 | 34,355.69 |

| Bucket | Items |
|---|---|
| [0.0, 5.0) | 6,637 |
| [5.0, 10.0) | 56,525 |
| [10.0, 15.0) | 58,762 |
| [15.0, 20.0) | 56,593 |
| [20.0, 30.0) | 63,081 |
| [30.0, 50.0) | 49,458 |
| [50.0, 100.0) | 28,107 |
| [100.0, 200.0) | 8,512 |
| [200.0, 500.0) | 2,561 |
| [500.0, inf) | 871 |
