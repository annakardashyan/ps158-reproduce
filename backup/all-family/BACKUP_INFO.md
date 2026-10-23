# All-family version backup

Frozen copies of the all-family scripts, README, processed CSV outputs, and figure as they existed before the families-with-children revision. The source ZIPs and extracted SCF inputs remain in the parent repository at `data/raw/`; this backup links to that unchanged input directory rather than duplicating its large raw files.

To rerun the preserved version, run `python3 get_data.py`, `python3 estimate_uncertainty.py`, then `python3 plot.py` from this directory.
