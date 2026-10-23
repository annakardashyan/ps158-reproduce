# POLISCI 158, Section 3, Option B: Wealth by parents' education

[Figure 1](figures/wealth_gap_by_education.svg) shows median net worth in 2025 dollars for U.S. SCF families with children, comparing those whose reference person has a bachelor's degree or more with those whose reference person has a high-school education or less, 1989–2025. The lower panel shows the ratio of the two medians. Whiskers in the upper panel are approximate 95% confidence intervals.

## Data and definitions

The data come from the Federal Reserve Board's [Survey of Consumer Finances public summary extracts](https://www.federalreserve.gov/econres/scfindex.htm), one CSV extract for each survey wave from 1989 through 2025. `get_data.py` downloads each original ZIP and extracts its CSV into `data/raw/`. It checks that the required `KIDS`, `EDCL`, `WGT`, and `NETWORTH` fields are present. The Fed's extracts express historical wealth in 2025 dollars; this project applies no additional inflation adjustment.

The population is **families with children**, defined by `KIDS > 0`. Education is the SCF family's reference person: `EDCL = 4` means bachelor's degree or higher, while `EDCL = 1` or `2` means high-school education or less. `EDCL = 3` (some college or associate degree) is excluded. The public extract supplies education for the reference person, not for both parents. The Fed harmonizes education categories across waves; its roster-based `KIDS` construction has a public-data limitation for foster children from 1995 forward, so that part of the child count may be underreported.

Within each of the five implicates, `plot.py` computes survey-weighted medians using `WGT`, then averages the five medians. The ratio is calculated within each implicate and then averaged. `estimate_uncertainty.py` uses SCF replicate weights for sampling variance and the five implicates for imputation variance. It applies `KIDS > 0` when assigning education groups, so both the point estimates and uncertainty calculations use the same population. Intervals are estimate ± 1.96 standard errors; they are approximate normal intervals and may extend below zero for some years. The script also computes a ratio interval, which is saved in the uncertainty CSV but not drawn in Figure 1.

For 2025, the median is **$628,430** (95% interval **$537,966–$718,894**) for the BA-or-more group and **$71,968** (**$50,060–$93,876**) for the high-school-or-less group. Their median ratio is **8.73×** (**5.97×–11.49×**).

There is no directly comparable Federal Reserve published table for medians restricted to `KIDS > 0` and split into these combined education groups. Published all-family education estimates are not validation targets for this figure.

## Rerun

From the repository root:

```sh
python3 get_data.py
python3 estimate_uncertainty.py
python3 plot.py
```

`estimate_uncertainty.py` requires NumPy and pandas, and SCF replicate-weight ZIPs in `data/raw/`. The scripts write `data/processed/education_wealth_gap.csv`, `data/processed/education_wealth_gap_uncertainty.csv`, and the figure linked above. The prior all-family version is preserved in `backup/all-family/`.
