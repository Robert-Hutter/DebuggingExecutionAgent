#!/usr/bin/env python3
"""
Evaluate a tracer CSV and compile runtime metrics.

Inputs:
  - A single CSV produced by Tracer.save(), containing fields:
    kind,name,start_ns,end_ns,wall_ns,cpu_start_ns,cpu_end_ns,cpu_ns,meta

Outputs:
  - Console tables (per-API and run-level summary)
  - Optional: Markdown and CSV reports

Usage:
  python evaluate_trace.py traces/with_adapter.csv
  python evaluate_trace.py traces/baseline.csv --unit ms --out-md report.md --out-csv report.csv
"""

from __future__ import annotations
import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# ---------- Units ----------

@dataclass(frozen=True)
class Unit:
    name: str      # 'ns', 'ms', 's'
    factor: float  # multiply nanoseconds by this factor

UNITS = {
    "ns": Unit("ns", 1.0),
    "ms": Unit("ms", 1e-6),
    "s":  Unit("s",  1e-9),
}

# ---------- Data loading ----------

@dataclass
class Row:
    kind: str
    name: str
    wall_ns: int

def load_rows(csv_path: Path) -> List[Row]:
    rows: List[Row] = []
    with csv_path.open() as f:
        r = csv.DictReader(f)
        for rec in r:
            rows.append(
                Row(
                    kind=rec["kind"],
                    name=rec["name"],
                    wall_ns=int(rec["wall_ns"]),
                )
            )
    return rows

# ---------- Computation ----------

@dataclass
class ApiMetrics:
    name: str
    count: int
    cumulative_ns: int
    mean_ns: float

@dataclass
class RunSummary:
    program_duration_ns: Optional[int]       # may be None if not present
    api_cumulative_ns: int
    non_api_ns: Optional[int]                # None if program_duration_ns is None
    api_share_pct: Optional[float]           # None if program_duration_ns is None

def compute_metrics(rows: List[Row]) -> Tuple[List[ApiMetrics], RunSummary]:
    # Per-API aggregation
    by_name: Dict[str, List[int]] = defaultdict(list)
    for r in rows:
        if r.kind == "api":
            by_name[r.name].append(r.wall_ns)

    per_api: List[ApiMetrics] = []
    for name, walls in by_name.items():
        total = sum(walls)
        count = len(walls)
        mean = total / count if count else 0.0
        per_api.append(ApiMetrics(name=name, count=count, cumulative_ns=total, mean_ns=mean))

    # Sort by largest cumulative duration
    per_api.sort(key=lambda m: m.cumulative_ns, reverse=True)

    # Program duration: choose the *largest* program span named "entire_run" if present,
    # otherwise the largest among all 'program' spans (robust to multiple spans).
    program_ns: Optional[int] = None
    program_spans = [r.wall_ns for r in rows if r.kind == "program" and r.name == "entire_run"]
    if not program_spans:
        program_spans = [r.wall_ns for r in rows if r.kind == "program"]
    if program_spans:
        program_ns = max(program_spans)

    api_total_ns = sum(m.cumulative_ns for m in per_api)
    non_api_ns: Optional[int] = None
    api_share_pct: Optional[float] = None
    if program_ns is not None:
        non_api_ns = program_ns - api_total_ns
        api_share_pct = (api_total_ns / program_ns * 100.0) if program_ns > 0 else 0.0

    summary = RunSummary(
        program_duration_ns=program_ns,
        api_cumulative_ns=api_total_ns,
        non_api_ns=non_api_ns,
        api_share_pct=api_share_pct,
    )
    return per_api, summary

# ---------- Formatting ----------

def fmt_duration(ns: float, unit: Unit) -> str:
    return f"{ns * unit.factor:,.3f} {unit.name}"

def fmt_float(x: Optional[float], digits: int = 2) -> str:
    return "n/a" if x is None else f"{x:.{digits}f}"

def render_table_per_api(per_api: List[ApiMetrics], unit: Unit) -> str:
    # Headers
    headers = [
        "API",
        "Invocation Count",
        f"Cumulative Duration ({unit.name})",
        f"Mean Duration ({unit.name})",
    ]
    # Rows
    rows = []
    for m in per_api:
        rows.append([
            m.name,
            f"{m.count:,}",
            f"{m.cumulative_ns * unit.factor:,.3f}",
            f"{m.mean_ns * unit.factor:,.3f}",
        ])
    return make_box_table(headers, rows)

def render_table_summary(summary: RunSummary, unit: Unit) -> str:
    headers = ["Metric", f"Value ({unit.name} / %)"]
    rows = [
        ["Program Duration", _fmt_ns(summary.program_duration_ns, unit)],
        ["API Cumulative Duration", _fmt_ns(summary.api_cumulative_ns, unit)],
        ["Non-API Duration (Program − API)", _fmt_ns(summary.non_api_ns, unit)],
        ["API Share of Program (%)", fmt_float(summary.api_share_pct, 2)],
    ]
    return make_box_table(headers, rows)

def _fmt_ns(ns_opt: Optional[int], unit: Unit) -> str:
    if ns_opt is None:
        return "n/a"
    return f"{ns_opt * unit.factor:,.3f}"

def make_box_table(headers: List[str], rows: List[List[str]]) -> str:
    # Compute column widths
    cols = len(headers)
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    # Helpers
    def hline(corners="+", hchar="─", sep="┼"):
        parts = []
        for w in widths:
            parts.append(hchar * (w + 2))
        return corners[0] + sep.join(parts) + corners[-1]

    def fmt_row(items: List[str], sep="│"):
        cells = []
        for i, cell in enumerate(items):
            s = str(cell)
            cells.append(" " + s.ljust(widths[i]) + " ")
        return sep + sep.join(cells) + sep

    # Build table
    out = []
    out.append(hline("+", "─", "┬"))
    out.append(fmt_row(headers, "│"))
    out.append(hline("+", "─", "┼"))
    for r in rows:
        out.append(fmt_row(r, "│"))
    out.append(hline("+", "─", "┴"))
    return "\n".join(out)

# ---------- Exports ----------

def export_markdown(per_api: List[ApiMetrics], summary: RunSummary, unit: Unit, path: Path):
    with path.open("w", encoding="utf-8") as f:
        # Per-API
        f.write("## Per-API Runtime Summary\n\n")
        f.write("| API | Invocation Count | Cumulative Duration (" + unit.name + ") | Mean Duration (" + unit.name + ") |\n")
        f.write("|---|---:|---:|---:|\n")
        for m in per_api:
            f.write(
                f"| {m.name} | {m.count:,} | {m.cumulative_ns * unit.factor:,.3f} | {m.mean_ns * unit.factor:,.3f} |\n"
            )
        # Summary
        f.write("\n## Run-Level Summary\n\n")
        f.write("| Metric | Value |\n")
        f.write("|---|---:|\n")
        f.write(f"| Program Duration ({unit.name}) | {_fmt_ns(summary.program_duration_ns, unit)} |\n")
        f.write(f"| API Cumulative Duration ({unit.name}) | {_fmt_ns(summary.api_cumulative_ns, unit)} |\n")
        f.write(f"| Non-API Duration ({unit.name}) | {_fmt_ns(summary.non_api_ns, unit)} |\n")
        f.write(f"| API Share of Program (%) | {fmt_float(summary.api_share_pct, 2)} |\n")

def export_csv(per_api: List[ApiMetrics], summary: RunSummary, unit: Unit, path: Path):
    # Per-API sheet
    per_api_path = path
    summary_path = path.with_name(path.stem + "_summary.csv")

    with per_api_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["API", "Invocation Count", f"Cumulative Duration ({unit.name})", f"Mean Duration ({unit.name})"])
        for m in per_api:
            w.writerow([m.name, m.count, f"{m.cumulative_ns * unit.factor:.6f}", f"{m.mean_ns * unit.factor:.6f}"])

    with summary_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Metric", "Value"])
        w.writerow([f"Program Duration ({unit.name})", _fmt_ns(summary.program_duration_ns, unit)])
        w.writerow([f"API Cumulative Duration ({unit.name})", _fmt_ns(summary.api_cumulative_ns, unit)])
        w.writerow([f"Non-API Duration ({unit.name})", _fmt_ns(summary.non_api_ns, unit)])
        w.writerow(["API Share of Program (%)", fmt_float(summary.api_share_pct, 2)])

# ---------- CLI ----------

def main():
    ap = argparse.ArgumentParser(description="Compile performance metrics from a tracer CSV.")
    ap.add_argument("csv_path", help="Path to a tracer CSV (e.g., traces/with_adapter.csv)")
    ap.add_argument("--unit", choices=list(UNITS.keys()), default="ms",
                    help="Display/output unit for durations (default: ms)")
    ap.add_argument("--out-md", help="Optional path to write a Markdown report")
    ap.add_argument("--out-csv", help="Optional path to write a CSV (per-API) plus a *_summary.csv file")
    args = ap.parse_args()

    unit = UNITS[args.unit]
    csv_path = Path(args.csv_path)
    rows = load_rows(csv_path)
    per_api, summary = compute_metrics(rows)

    # Console output
    print("\nPER-API RUNTIME SUMMARY")
    print(render_table_per_api(per_api, unit))
    print("\nRUN-LEVEL SUMMARY")
    print(render_table_summary(summary, unit))

    # Optional exports
    if args.out_md:
        export_markdown(per_api, summary, unit, Path(args.out_md))
        print(f"\nMarkdown report written to: {args.out_md}")
    if args.out_csv:
        export_csv(per_api, summary, unit, Path(args.out_csv))
        print(f"CSV reports written to: {args.out_csv} and {Path(args.out_csv).with_name(Path(args.out_csv).stem + '_summary.csv')}")

if __name__ == "__main__":
    main()