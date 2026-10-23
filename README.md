# POLISCI 158, Section 3, Option B: wealth by parents' education

[Figure 1](https://github.com/annakardashyan/ps158-reproduce/blob/main/figures/wealth_gap_by_education.svg) ([image](https://github.com/annakardashyan/ps158-reproduce/raw/main/figures/wealth_gap_by_education.svg))

**Figure 1** shows median net worth in 2025 dollars for U.S. families with children whose SCF reference person has a bachelor's degree or more, compared with families whose reference person has a high-school education or less, 1989–2025. Panel (b) shows the ratio of the two medians.

## Where the data come from

The data are the Federal Reserve Board's **Survey of Consumer Finances (SCF), summary extract public data**: one CSV summary extract for each survey wave, every three years from 1989 through 2025. The original ZIP files are downloaded from the [Federal Reserve SCF data page](https://www.federalreserve.gov/econres/scfindex.htm) by `get_data.py`; the script extracts the CSVs into `data/raw/`. These are the Federal Reserve's files, not a third-party redistribution.

The 2025 wave is the latest survey included in this project. The Fed's public summary extracts report historical wealth in the latest survey's dollars, so these values are in **2025 dollars**. The project applies no additional inflation adjustment.

## How to rerun

From the repository root:

```sh
python3 get_data.py
python3 estimate_uncertainty.py
python3 plot.py
```

`get_data.py` downloads the SCF summary-extract ZIPs and extracts the CSVs. `estimate_uncertainty.py` computes confidence intervals using the SCF replicate-weight files and requires NumPy and pandas. `plot.py` reads the downloaded data and writes `figures/wealth_gap_by_education.svg` and the processed estimates in `data/processed/`.

No estimates are typed into the plotting script. The survey years and dollar values come from the downloaded SCF data.

## Choices

- **Families with children:** families with at least one child in the household (`KIDS > 0`).
- **Education:** the SCF summary extract records the education of the family's *reference person* only (`EDCL`), not both parents. “BA or more” is `EDCL = 4`; “high school or less” is `EDCL = 1` (no high-school diploma or GED) or `2` (high-school diploma or GED). Families with some college or an associate degree (`EDCL = 3`) are excluded.
- **Survey weights:** each family appears five times in the data, once per imputation (“implicate”). For each implicate, the median is weighted with the survey weight `WGT`; the figure shows the average of the five medians. The ratio is computed within each implicate and then averaged.
- **Confidence intervals:** `estimate_uncertainty.py` uses the SCF replicate weights for sampling variability and the five implicates for imputation variability. It applies the same `KIDS > 0` filter and education groups as the point estimates. Intervals are approximate 95% intervals, calculated as the estimate plus or minus 1.96 standard errors. The ratio interval is in the processed uncertainty CSV but is not drawn in Figure 1.
- **Constant dollars:** all years are in **2025 dollars**, as supplied in the Fed's current summary extracts. No additional inflation adjustment is applied.

## Latest estimates and comparison

For 2025, the median net worth is **$628,430** (approximate 95% interval: **$537,966–$718,894**) for families whose reference person has a BA or more, and **$71,968** (**$50,060–$93,876**) for families whose reference person has a high-school education or less. The ratio of the medians is **8.73×** (approximate 95% interval: **5.97×–11.49×**).

The Fed does not publish median net worth for this exact population of families with children split into these combined education groups. Published SCF figures for all families by reference-person education are not directly comparable and are not validation targets for Figure 1. The education measure describes the reference person, rather than both parents. The Fed also notes a public-data limitation in identifying foster children from 1995 onward, so `KIDS` may undercount them in those waves.

## Files

| File | Description |
| --- | --- |
| `get_data.py` | Downloads and extracts the Federal Reserve SCF summary extracts; checks for the required variables. |
| `plot.py` | Computes weighted medians for families with children and draws Figure 1. |
| `estimate_uncertainty.py` | Estimates standard errors and approximate 95% confidence intervals. |
| `figures/wealth_gap_by_education.svg` | Figure 1. |
| `data/processed/education_wealth_gap.csv` | Point estimates shown in Figure 1. |
| `data/processed/education_wealth_gap_uncertainty.csv` | Standard errors and confidence interval bounds. |
| `backup/all-family/` | Preserved copy of the prior all-family scripts, README, figure, and processed outputs. |

Repository: [annakardashyan/ps158-reproduce](https://github.com/annakardashyan/ps158-reproduce).
