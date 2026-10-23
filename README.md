# POLISCI 158, Section 3, Option B: Wealth by parents' education

[Figure 1](figures/wealth_gap_by_education.svg) shows median net worth of U.S. families by the education of the SCF reference person, 1989–2025. The upper panel compares families with a bachelor's degree or more to families with a high-school education or less; the lower panel shows the ratio of those medians. The figure is in 2025 dollars and includes 95% confidence intervals.

## Where the data come from

The data are the Federal Reserve Board's [Survey of Consumer Finances (SCF) public summary extracts](https://www.federalreserve.gov/econres/scfindex.htm), one CSV extract for each survey wave from 1989 through 2025. `get_data.py` downloads each original ZIP from the Federal Reserve and extracts its CSV into `data/raw/`. These are the Fed's public files, not a third-party redistribution. The extracts express historical wealth in the latest survey's dollars (2025 dollars for this series); the scripts apply no additional inflation adjustment.

## Choices

- **Families:** All SCF families, not only families with children.
- **Education:** The extract identifies education for the family's reference person, not both parents. `EDCL = 4` is bachelor's degree or more; `EDCL = 1` or `2` is high-school education or less. `EDCL = 3` (some college or an associate degree) is excluded.
- **Weights and implicates:** Within each of the five SCF implicates, `plot.py` calculates medians using the survey weight `WGT`, then averages the five medians. The ratio is calculated for each implicate and then averaged.
- **Uncertainty:** `estimate_uncertainty.py` uses the Fed's replicate weights for sampling variability and the five implicates for imputation variability. The plotted whiskers are approximate 95% intervals, computed as estimate ± 1.96 standard errors.

## Check against the Fed's published numbers

As a validation, the 2025 public extract's median net worth for families whose reference person has a college degree is **$511,660**. The Federal Reserve's 2025 SCF report, Table 2, reports **$505,400** for the corresponding category, a difference of **$6,260 (1.24%)**. Across the comparable Table 2 measures checked, the largest absolute difference is the college-degree mean: **$2,240,358** from the public extract versus **$2,263,300** in the table, a difference of **$22,942 (about 1.0%)**. The table does not report a combined high-school-or-less category. Public extract calculations can differ from the Fed's published estimates because the public files are adjusted to protect respondent confidentiality.

The 2025 estimated median is **$511,660** (approximate 95% interval: **$446,870–$576,450**) for college-degree families and **$80,878** (**$67,169–$94,587**) for high-school-or-less families. The median difference is **$430,782** (**$364,654–$496,910**).

One historical point needs caution: the public extract gives a 2007 college-group median of about **$509,676 in 2025 dollars**, while the original 2007 SCF Bulletin table reports **$280,800 in 2007 dollars**. Those figures do not reconcile through a simple inflation adjustment. The discrepancy may reflect revisions, disclosure adjustments, or weighting differences; its cause has not been established.

As a second comparison, the Census Bureau's [SIPP household wealth report](https://www2.census.gov/library/publications/2026/demo/p70br-218.pdf) also finds higher median wealth at higher education levels. Its amounts are not directly comparable: SIPP measures households and education of the household's most educated member, and uses a different wealth definition.

## How to rerun

From the repository root, with Python 3:

```sh
python3 get_data.py
python3 plot.py
```

`get_data.py` downloads and extracts the SCF summary CSV ZIPs. `plot.py` writes `data/processed/education_wealth_gap.csv` and `figures/wealth_gap_by_education.svg`. To recompute the confidence intervals, run `python3 estimate_uncertainty.py` before `python3 plot.py`; this step requires NumPy and pandas and the SCF replicate-weight ZIP files in `data/raw/`. (The checked-in data files can be used without downloading them again.)

## Repository files

| File | Description |
| --- | --- |
| `get_data.py` | Downloads and extracts the Federal Reserve summary extracts. |
| `plot.py` | Computes weighted medians and draws Figure 1. |
| `estimate_uncertainty.py` | Estimates standard errors and 95% intervals. |
| `figures/wealth_gap_by_education.svg` | Black-and-white Figure 1, with caption and source note. |
| `data/processed/education_wealth_gap.csv` | Values plotted in Figure 1. |
| `data/processed/education_wealth_gap_uncertainty.csv` | Standard errors and confidence interval bounds. |

Repository: [annakardashyan/ps158-reproduce](https://github.com/annakardashyan/ps158-reproduce).
