#!/usr/bin/env python3
"""Plot median net worth for SCF families with children by reference-person education.

Reads the Federal Reserve's public summary-extract CSV ZIPs from data/raw,
averages five implicate-specific weighted medians, and writes a result CSV and
an SVG figure. Uses only Python's standard library.
"""

import csv
import html
import math
from pathlib import Path
from statistics import mean
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
RESULTS = ROOT / "data" / "processed" / "education_wealth_gap.csv"
UNCERTAINTY = ROOT / "data" / "processed" / "education_wealth_gap_uncertainty.csv"
FIGURE = ROOT / "figures" / "wealth_gap_by_education.svg"
YEARS = list(range(1989, 2026, 3))


def number(row, field):
    value = row.get(field, "").strip()
    if not value:
        return None
    try:
        value = float(value)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def implicate(row, fields):
    if "X1" in fields:  # 1989 identifier includes the implicate as its last digit
        value = number(row, "X1")
        return int(value) % 10 if value is not None else None
    y1, yy1 = number(row, "Y1"), number(row, "YY1")
    return int(y1 - 10 * yy1) if y1 is not None and yy1 is not None else None


def weighted_median(observations):
    observations = sorted((value, weight) for value, weight in observations
                          if value is not None and weight is not None and weight > 0)
    total_weight = sum(weight for _, weight in observations)
    if not observations or total_weight <= 0:
        raise ValueError("A group has no valid observations with positive weights")
    midpoint = total_weight / 2
    cumulative = 0.0
    for value, weight in observations:
        cumulative += weight
        if cumulative >= midpoint:
            return value
    return observations[-1][0]


def read_year(year):
    path = RAW / f"scf_{year}_summary_extract_csv.zip"
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}; run get_data.py first")
    implicate_rows = {}
    with ZipFile(path) as archive:
        csv_names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(csv_names) != 1:
            raise ValueError(f"Expected one CSV in {path.name}, found {csv_names}")
        with archive.open(csv_names[0]) as source:
            import io
            text = io.TextIOWrapper(source, encoding="utf-8-sig", newline="")
            reader = csv.DictReader(text)
            fields = {field.upper() for field in (reader.fieldnames or [])}
            required = {"WGT", "EDCL", "NETWORTH", "KIDS"}
            if not required.issubset(fields):
                raise ValueError(f"{path.name} is missing required columns: {required - fields}")
            if not ("X1" in fields or {"Y1", "YY1"}.issubset(fields)):
                raise ValueError(f"{path.name} has no recognized implicate identifier")
            for raw_row in reader:
                row = {key.upper(): value for key, value in raw_row.items() if key}
                imp = implicate(row, fields)
                group = number(row, "EDCL")
                kids = number(row, "KIDS")
                wealth = number(row, "NETWORTH")
                weight = number(row, "WGT")
                if imp is None or group is None or kids is None or wealth is None or weight is None:
                    continue
                if kids <= 0:
                    continue
                if int(group) == 4:
                    key = "college"
                elif int(group) in (1, 2):
                    key = "high_school_or_less"
                else:
                    continue  # EDCL 3: some college/associate degree
                implicate_rows.setdefault((imp, key), []).append((wealth, weight))

    medians = {}
    ratios = []
    implicates = sorted({imp for imp, _ in implicate_rows})
    if implicates != [1, 2, 3, 4, 5]:
        raise ValueError(f"{year}: expected five implicates, found {implicates}")
    for key in ("college", "high_school_or_less"):
        per_implicate = [weighted_median(implicate_rows[(imp, key)]) for imp in implicates]
        medians[key] = mean(per_implicate)
    for imp in implicates:
        college = weighted_median(implicate_rows[(imp, "college")])
        low = weighted_median(implicate_rows[(imp, "high_school_or_less")])
        ratios.append(college / low)
    medians["ratio"] = mean(ratios)
    return medians


def svg_text(x, y, text, size=14, fill="#273244", weight="normal", anchor="start"):
    return (f'<text x="{x}" y="{y}" font-family="Arial, Helvetica, sans-serif" '
            f'font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}">{html.escape(str(text))}</text>')


def make_svg(results):
    width, height = 1120, 830
    x0, x1 = 100, 1060
    top_y0, top_y1 = 130, 400
    bot_y0, bot_y1 = 500, 675
    years = [row["year"] for row in results]
    max_median = max(max(r["college"], r["high_school_or_less"]) for r in results)
    max_ratio = max(r["ratio"] for r in results)
    for row in results:
        max_median = max(max_median, row.get("college_ci_upper", 0),
                         row.get("high_school_or_less_ci_upper", 0))
        max_ratio = max(max_ratio, row.get("ratio_ci_upper", 0))
    med_max = max(600_000, math.ceil(max_median / 100_000) * 100_000)
    ratio_max = max(8, math.ceil(max_ratio / 2) * 2)
    x_for = lambda year: x0 + (year - years[0]) / (years[-1] - years[0]) * (x1 - x0)
    y_money = lambda value: top_y1 - value / med_max * (top_y1 - top_y0)
    y_ratio = lambda value: bot_y1 - value / ratio_max * (bot_y1 - bot_y0)
    black, gray = "#111111", "#555555"
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="#FFFFFF"/>',
             svg_text(60, 40, "Median family net worth · thousands of 2025 dollars", 16, black, "bold")]
    for x, label, color, dash, marker in ((112, "BA or more (reference person)", black, "", "circle"),
                                          (435, "High school or less (reference person)", gray, "8 5", "square")):
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        parts.append(f'<line x1="{x}" y1="76" x2="{x+28}" y2="76" stroke="{color}" stroke-width="2.8"{dash_attr}/>')
        if marker == "circle":
            parts.append(f'<circle cx="{x+14}" cy="76" r="3.5" fill="white" stroke="{color}" stroke-width="2"/>')
        else:
            parts.append(f'<rect x="{x+10.5}" y="72.5" width="7" height="7" fill="white" stroke="{color}" stroke-width="2"/>')
        parts.append(svg_text(x+36, 81, label, 13, "#222222"))
    for tick in range(0, int(med_max / 1000) + 1, 100):
        y = y_money(tick * 1000)
        parts += [f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="#D8D8D8"/>',
                  svg_text(x0-14, y+5, f"${tick:,}k", 12, "#333333", anchor="end")]
    for year in years:
        x=x_for(year)
        parts += [f'<line x1="{x:.1f}" y1="{top_y0}" x2="{x:.1f}" y2="{top_y1}" stroke="#EEEEEE"/>',
                  svg_text(x, top_y1+22, year, 11, "#333333", anchor="middle")]
    for key, color, dash, marker in (("college", black, "", "circle"),
                                     ("high_school_or_less", gray, "8 5", "square")):
        low_key, high_key = f"{key}_ci_lower", f"{key}_ci_upper"
        if all(low_key in r and high_key in r for r in results):
            for row in results:
                x=x_for(row["year"]); lo=y_money(max(0,row[low_key])); hi=y_money(max(0,row[high_key]))
                parts.append(f'<line x1="{x:.1f}" y1="{lo:.1f}" x2="{x:.1f}" y2="{hi:.1f}" stroke="{color}" stroke-width="1"/>')
        coords=" ".join(f'{x_for(r["year"]):.1f},{y_money(r[key]):.1f}' for r in results)
        dash_attr=f' stroke-dasharray="{dash}"' if dash else ""
        parts.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="2.8"{dash_attr}/>')
        for row in results:
            x=x_for(row["year"]); y=y_money(row[key])
            if marker == "circle":
                parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="white" stroke="{color}" stroke-width="2"/>')
            else:
                parts.append(f'<rect x="{x-3.5:.1f}" y="{y-3.5:.1f}" width="7" height="7" fill="white" stroke="{color}" stroke-width="2"/>')
    latest=results[-1]; lx=x_for(latest["year"])
    parts += [svg_text(lx-8,y_money(latest["college"])-12,f'${latest["college"]/1000:,.0f}k',12,black,"bold","end"),
              svg_text(lx-8,y_money(latest["high_school_or_less"])+19,f'${latest["high_school_or_less"]/1000:,.0f}k',12,gray,"bold","end"),
              svg_text(60,463,"Median wealth ratio · college group ÷ high-school-or-less group",15,black,"bold")]
    for tick in range(0,ratio_max+1,2):
        y=y_ratio(tick)
        parts += [f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="#D8D8D8"/>',
                  svg_text(x0-14,y+5,f"{tick}×",12,"#333333",anchor="end")]
    coords=" ".join(f'{x_for(r["year"]):.1f},{y_ratio(r["ratio"]):.1f}' for r in results)
    parts.append(f'<polyline points="{coords}" fill="none" stroke="{black}" stroke-width="2.8"/>')
    for row in results:
        x=x_for(row["year"]); y=y_ratio(row["ratio"])
        parts += [f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="white" stroke="{black}" stroke-width="2"/>',
                  svg_text(x,bot_y1+22,row["year"],11,"#333333",anchor="middle")]
    parts += [svg_text(lx-8,y_ratio(latest["ratio"])-12,f'{latest["ratio"]:.1f}×',13,black,"bold","end"),
              '<line x1="60" y1="720" x2="1060" y2="720" stroke="#111111" stroke-width="1"/>',
              svg_text(60,748,"Figure 1. Median net worth of families with children by reference-person education, 1989–2025.",13,black,"bold"),
              svg_text(60,776,"Source: Federal Reserve Board, Survey of Consumer Finances (SCF), public summary extracts, 1989–2025.",12,"#222222"),
              svg_text(60,800,"Note: Families with children (KIDS > 0); weighted medians averaged across five implicates. Whiskers show approximate 95% intervals.",11,"#333333"),
              svg_text(60,818,"BA or more (EDCL=4) versus high school or less (EDCL=1 or 2); EDCL=3 excluded. Dollars are 2025 dollars.",11,"#333333"),
              '</svg>']
    return "\n".join(parts)


def main():
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    results = []
    for year in YEARS:
        medians = read_year(year)
        low = medians["high_school_or_less"]
        college = medians["college"]
        results.append({"year": year, "college": college,
                        "high_school_or_less": low,
                        "gap": college - low,
                        "ratio": medians["ratio"]})
    if UNCERTAINTY.exists():
        with UNCERTAINTY.open(newline="", encoding="utf-8") as stream:
            uncertainty = {int(row["year"]): row for row in csv.DictReader(stream)}
        for row in results:
            se_row = uncertainty.get(row["year"])
            if se_row:
                for key in ("college", "high_school_or_less", "ratio"):
                    row[f"{key}_ci_lower"] = float(se_row[f"{key}_ci_lower"])
                    row[f"{key}_ci_upper"] = float(se_row[f"{key}_ci_upper"])
    with RESULTS.open("w", newline="", encoding="utf-8") as stream:
        columns = ["year", "population_filter", "college_median_2025_usd",
                   "high_school_or_less_median_2025_usd",
                   "median_gap_2025_usd", "median_ratio"]
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row in results:
            writer.writerow({
                "year": row["year"],
                "population_filter": "KIDS > 0",
                "college_median_2025_usd": row["college"],
                "high_school_or_less_median_2025_usd": row["high_school_or_less"],
                "median_gap_2025_usd": row["gap"],
                "median_ratio": row["ratio"],
            })
    FIGURE.write_text(make_svg(results), encoding="utf-8")
    print(f"Wrote {RESULTS}")
    print(f"Wrote {FIGURE}")


if __name__ == "__main__":
    main()
