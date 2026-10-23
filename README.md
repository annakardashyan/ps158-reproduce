# SCF education and wealth gap

This project makes a first figure of U.S. family net worth by education of the SCF reference person, across survey waves from 1989 to 2025. The figure is `figures/wealth_gap_by_education.svg`; it shows weighted median net worth and the college-to-high-school-or-less median ratio. Dollar values are in 2025 dollars.

The data come from the Federal Reserve's [Survey of Consumer Finances (SCF)](https://www.federalreserve.gov/econres/scfindex.htm) public summary-extract CSVs. The scripts use all families, with or without children; education is the reference person's attainment. “College” means a college degree or higher, and “high school or less” includes no diploma and a high school diploma. The some-college group is excluded. Weighted medians are calculated separately for each of the five imputation implicates and then averaged.

## Rerun

From the repository root, with Python 3:

```sh
python3 get_data.py
python3 plot.py
```

`get_data.py` downloads each wave's CSV ZIP if needed and extracts its CSV to `data/raw/`. `plot.py` reads those ZIPs and writes the figure plus `data/processed/education_wealth_gap.csv`.
