#!/usr/bin/env python3
"""Estimate SCF median uncertainty from implicates and replicate weights.

Requires pandas and NumPy. Uses the Federal Reserve's summary extracts for
point values and merges the matching first-implicate cases to each wave's
replicate-weight Stata file.
"""

import csv
from io import BytesIO
from pathlib import Path
from statistics import mean, stdev
from zipfile import ZipFile

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
OUTPUT = ROOT / "data" / "processed" / "education_wealth_gap_uncertainty.csv"
YEARS = list(range(1989, 2026, 3))
REPLICATES = 999


def weighted_median(values, weights):
    values = np.asarray(values, dtype=np.float64)
    weights = np.asarray(weights, dtype=np.float64)
    valid = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    values, weights = values[valid], weights[valid]
    if not len(values) or weights.sum() <= 0:
        raise ValueError("Cannot estimate a weighted median from an empty group")
    order = np.argsort(values, kind="mergesort")
    values, weights = values[order], weights[order]
    index = np.searchsorted(np.cumsum(weights), weights.sum() / 2, side="left")
    return float(values[min(index, len(values) - 1)])


def read_extract(year):
    path = RAW / f"scf_{year}_summary_extract_csv.zip"
    with ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(names) != 1:
            raise ValueError(f"Expected one CSV in {path.name}; found {names}")
        frame = pd.read_csv(archive.open(names[0]))
    frame.columns = [str(column).lower() for column in frame.columns]
    required = {"kids", "edcl", "wgt", "networth"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{path.name} is missing required fields: {sorted(missing)}")
    if frame["kids"].isna().any():
        raise ValueError(f"{path.name} has missing KIDS values")
    if "x1" in frame:
        id_col = "x1"
        frame["implicate"] = frame[id_col].astype("int64") % 10
    else:
        id_col = "y1"
        frame["implicate"] = (frame["y1"].astype("int64")
                              - 10 * frame["yy1"].astype("int64"))
    has_children = pd.to_numeric(frame["kids"], errors="coerce").gt(0)
    frame["education_group"] = np.select(
        [has_children & frame["edcl"].eq(4), has_children & frame["edcl"].isin([1, 2])],
        ["college", "high_school_or_less"], default="excluded")
    return frame, id_col


def read_replicates(year):
    path = RAW / f"scf_{year}_replicate_weights_stata.zip"
    with ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith(".dta")]
        if len(names) != 1:
            raise ValueError(f"Expected one Stata file in {path.name}; found {names}")
        frame = pd.read_stata(BytesIO(archive.read(names[0])), convert_categoricals=False)
    frame.columns = [str(column).lower() for column in frame.columns]
    return frame


def sample_variance_from_replicates(first_implicate, rep_frame, id_col):
    weight_cols = [f"wt1b{i}" for i in range(1, REPLICATES + 1)]
    mult_cols = [f"mm{i}" for i in range(1, REPLICATES + 1)]
    missing = (set(weight_cols) | set(mult_cols) | {id_col}) - set(rep_frame.columns)
    if missing:
        raise ValueError(f"Replicate file is missing expected fields: {sorted(missing)[:8]}")
    first = first_implicate.copy()
    reps = rep_frame[[id_col] + weight_cols + mult_cols].copy()
    first[id_col] = first[id_col].astype("int64")
    reps[id_col] = reps[id_col].astype("int64")
    joined = first.merge(reps, on=id_col, how="inner", validate="one_to_one")
    if len(joined) != len(first):
        raise ValueError(f"Replicate weights did not match all first-implicate rows for {id_col}")

    result = {}
    for group in ("college", "high_school_or_less"):
        # education_group was assigned only after KIDS > 0 in read_extract;
        # this therefore applies the identical target population to all 999 replicates.
        subset = joined.loc[joined["education_group"] == group].copy()
        if subset.empty:
            raise ValueError(f"No records for {group}")
        wealth = subset["networth"].to_numpy(dtype=np.float64)
        wealth_order = np.argsort(wealth, kind="mergesort")
        wealth = wealth[wealth_order]
        weights = subset[weight_cols].to_numpy(dtype=np.float64)[wealth_order, :]
        multiplicity = subset[mult_cols].to_numpy(dtype=np.float64)[wealth_order, :]
        weights = np.nan_to_num(weights, nan=0.0, posinf=0.0, neginf=0.0)
        multiplicity = np.nan_to_num(multiplicity, nan=0.0, posinf=0.0, neginf=0.0)
        weights *= multiplicity
        totals = weights.sum(axis=0)
        if np.any(totals <= 0):
            raise ValueError(f"At least one replicate has no weight for {group}")
        cumulative = np.cumsum(weights, axis=0)
        med_indices = (cumulative >= totals[None, :] / 2).argmax(axis=0)
        replicate_medians = wealth[med_indices]
        if len(replicate_medians) != REPLICATES:
            raise ValueError(f"Expected {REPLICATES} replicate medians for {group}")
        result[group] = replicate_medians
    result["gap"] = result["college"] - result["high_school_or_less"]
    result["ratio"] = result["college"] / result["high_school_or_less"]
    return result


def estimate_year(year):
    data, id_col = read_extract(year)
    implicates = sorted(data["implicate"].dropna().astype(int).unique().tolist())
    if implicates != [1, 2, 3, 4, 5]:
        raise ValueError(f"{year}: expected five implicates, found {implicates}")

    medians = {key: [] for key in ("college", "high_school_or_less")}
    for implicate in implicates:
        subset = data.loc[data["implicate"] == implicate]
        for group in medians:
            rows = subset.loc[subset["education_group"] == group]
            medians[group].append(weighted_median(rows["networth"], rows["wgt"]))
    points = {key: mean(values) for key, values in medians.items()}
    gap_by_imp = [college - low for college, low in zip(medians["college"], medians["high_school_or_less"])]
    ratio_by_imp = [college / low for college, low in zip(medians["college"], medians["high_school_or_less"])]

    first = data.loc[data["implicate"] == 1].copy()
    replicate_medians = sample_variance_from_replicates(first, read_replicates(year), id_col)
    sample_vars = {key: float(np.var(values, ddof=1)) for key, values in replicate_medians.items()}
    imp_vars = {
        "college": stdev(medians["college"]) ** 2,
        "high_school_or_less": stdev(medians["high_school_or_less"]) ** 2,
        "gap": stdev(gap_by_imp) ** 2,
        "ratio": stdev(ratio_by_imp) ** 2,
    }
    estimates = {**points, "gap": points["college"] - points["high_school_or_less"],
                 "ratio": mean(ratio_by_imp)}
    output = {"year": year, "population_filter": "KIDS > 0"}
    for key, estimate in estimates.items():
        se = (sample_vars[key] + (6 / 5) * imp_vars[key]) ** 0.5
        output[f"{key}_se"] = se
        output[f"{key}_ci_lower"] = estimate - 1.96 * se
        output[f"{key}_ci_upper"] = estimate + 1.96 * se
    return output


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for year in YEARS:
        print(f"Estimating standard errors for {year}...", flush=True)
        rows.append(estimate_year(year))
    with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
