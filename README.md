# SCF education and wealth gap

This project reproduces a figure of U.S. family median net worth by the SCF reference person’s education from 1989 to 2025. The figure is `figures/wealth_gap_by_education.svg` and reports 2025 dollars.

Data come from the Federal Reserve’s [Survey of Consumer Finances public summary extracts](https://www.federalreserve.gov/econres/scfindex.htm). The comparison uses all families, college degree or higher versus high school or less; the some-college group is excluded.

To download the data and redraw the figure from the repository root:

```sh
python3 get_data.py
python3 plot.py
```
