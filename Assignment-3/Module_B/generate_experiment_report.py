#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class StageStats:
    total_requests: int | None = None
    failures: int | None = None
    failure_rate: float | None = None
    avg_ms: float | None = None
    p50_ms: float | None = None
    p95_ms: float | None = None
    p99_ms: float | None = None
    max_ms: float | None = None
    rps: float | None = None


def _to_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def _to_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _fmt_int(value: int | None) -> str:
    return "N/A" if value is None else f"{value:,}"


def _fmt_float(value: float | None, digits: int = 2) -> str:
    return "N/A" if value is None else f"{value:.{digits}f}"


def _read_aggregated_stats(csv_path: Path) -> StageStats | None:
    if not csv_path.exists():
        return None

    with csv_path.open(newline="", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        aggregated = None
        for row in reader:
            if row.get("Name") == "Aggregated" or row.get("Type") == "Aggregated":
                aggregated = row
                break

    if not aggregated:
        return None

    total = _to_int(aggregated.get("Request Count"))
    failures = _to_int(aggregated.get("Failure Count"))
    failure_rate = None
    if total and failures is not None:
        failure_rate = (failures / total) * 100.0

    return StageStats(
        total_requests=total,
        failures=failures,
        failure_rate=failure_rate,
        avg_ms=_to_float(aggregated.get("Average Response Time")),
        p50_ms=_to_float(aggregated.get("50%")),
        p95_ms=_to_float(aggregated.get("95%")),
        p99_ms=_to_float(aggregated.get("99%")),
        max_ms=_to_float(aggregated.get("Max Response Time")),
        rps=_to_float(aggregated.get("Requests/s")),
    )


def _read_failures(csv_path: Path) -> list[dict[str, Any]]:
    if not csv_path.exists():
        return []

    with csv_path.open(newline="", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        rows = []
        for row in reader:
            try:
                occ = int(row.get("Occurrences", "0") or 0)
            except ValueError:
                occ = 0
            rows.append(
                {
                    "method": row.get("Method", ""),
                    "name": row.get("Name", ""),
                    "error": row.get("Error", ""),
                    "occurrences": occ,
                }
            )

    rows.sort(key=lambda item: item["occurrences"], reverse=True)
    return rows


def _read_exceptions_count(csv_path: Path) -> int | None:
    if not csv_path.exists():
        return None

    with csv_path.open(newline="", encoding="utf-8") as fp:
        reader = csv.reader(fp)
        rows = list(reader)
    if not rows:
        return 0
    return max(len(rows) - 1, 0)


def _read_acid(json_path: Path) -> dict[str, Any] | None:
    if not json_path.exists():
        return None
    try:
        return json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _acid_summary(acid_payload: dict[str, Any] | None) -> tuple[str, list[tuple[str, int]]]:
    if not acid_payload:
        return "missing", []

    status = "violations" if acid_payload.get("has_violations") else "clean"
    checks = acid_payload.get("checks", {}) or {}
    nonzero = []
    for check_name, check_data in checks.items():
        violations = int(check_data.get("violations", 0) or 0)
        if violations > 0:
            nonzero.append((check_name, violations))
    nonzero.sort(key=lambda item: item[1], reverse=True)
    return status, nonzero


def _render_stage_block(title: str, stats: StageStats | None, failures: list[dict[str, Any]], exceptions: int | None) -> str:
    lines = [f"## {title}"]
    if not stats:
        lines.append("- Stats: missing")
        lines.append("")
        return "\n".join(lines)

    lines.extend(
        [
            f"- Total requests: {_fmt_int(stats.total_requests)}",
            f"- Failures: {_fmt_int(stats.failures)} ({_fmt_float(stats.failure_rate)}%)",
            f"- Avg response time: {_fmt_float(stats.avg_ms)} ms",
            f"- p50/p95/p99: {_fmt_float(stats.p50_ms)} / {_fmt_float(stats.p95_ms)} / {_fmt_float(stats.p99_ms)} ms",
            f"- Max response time: {_fmt_float(stats.max_ms)} ms",
            f"- Throughput: {_fmt_float(stats.rps)} req/s",
            f"- Exceptions: {'N/A' if exceptions is None else exceptions}",
        ]
    )

    if failures:
        lines.append("- Top failures:")
        for row in failures[:5]:
            lines.append(
                f"  - {row['method']} {row['name']} -> {row['occurrences']} | {row['error']}"
            )
    else:
        lines.append("- Top failures: none")

    lines.append("")
    return "\n".join(lines)


def _render_acid_block(label: str, payload: dict[str, Any] | None) -> str:
    status, nonzero = _acid_summary(payload)
    lines = [f"## {label}"]

    if status == "missing":
        lines.append("- Snapshot: missing")
        lines.append("")
        return "\n".join(lines)

    stage_name = payload.get("stage", "unknown")
    ts = payload.get("timestamp_utc", "unknown")
    lines.append(f"- Snapshot stage: {stage_name}")
    lines.append(f"- Timestamp (UTC): {ts}")
    lines.append(f"- Result: {'no violations' if status == 'clean' else 'violations found'}")

    if nonzero:
        lines.append("- Violating checks:")
        for check_name, count in nonzero[:8]:
            lines.append(f"  - {check_name}: {count}")
    else:
        lines.append("- Violating checks: none")

    lines.append("")
    return "\n".join(lines)


def generate_report(exp_dir: Path, output_name: str = "overall_report.md") -> Path:
    artifact_rel = f"artifacts/{exp_dir.name}"
    concurrent_stats = _read_aggregated_stats(exp_dir / "concurrent_stage_stats.csv")
    race_stats = _read_aggregated_stats(exp_dir / "race_stage_stats.csv")

    concurrent_failures = _read_failures(exp_dir / "concurrent_stage_failures.csv")
    race_failures = _read_failures(exp_dir / "race_stage_failures.csv")

    concurrent_exceptions = _read_exceptions_count(exp_dir / "concurrent_stage_exceptions.csv")
    race_exceptions = _read_exceptions_count(exp_dir / "race_stage_exceptions.csv")

    acid_b = _read_acid(exp_dir / "acid_stage_b.json")
    acid_c = _read_acid(exp_dir / "acid_stage_c.json")
    acid_d = _read_acid(exp_dir / "acid_stage_d.json")

    lines = [
        f"# Experiment Summary ({exp_dir.name})",
        "",
        f"- Artifact folder: `{artifact_rel}`",
        "",
        _render_stage_block("Concurrent Stage", concurrent_stats, concurrent_failures, concurrent_exceptions),
        _render_stage_block("Race Stage", race_stats, race_failures, race_exceptions),
        _render_acid_block("ACID Stage B (Post-Concurrent)", acid_b),
        _render_acid_block("ACID Stage C (Post-Race)", acid_c),
        _render_acid_block("ACID Stage D (Durability/Post-Restart)", acid_d),
    ]

    output_path = exp_dir / output_name
    output_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate markdown summary report(s) for Module B experiment artifacts.")
    parser.add_argument(
        "--artifact-dir",
        default=str(Path(__file__).resolve().parent / "artifacts"),
        help="Path to artifacts root or a single experiment folder.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate reports for all experiment subfolders under artifact-dir.",
    )
    parser.add_argument(
        "--output-name",
        default="overall_report.md",
        help="Output markdown filename to create in each experiment folder.",
    )
    args = parser.parse_args()

    target = Path(args.artifact_dir).resolve()

    generated: list[Path] = []
    if args.all:
        if not target.exists():
            raise FileNotFoundError(f"Artifact root not found: {target}")
        for candidate in sorted(target.iterdir()):
            if candidate.is_dir():
                generated.append(generate_report(candidate, output_name=args.output_name))
    else:
        if target.is_dir() and any(p.name.endswith("_stage_stats.csv") for p in target.iterdir() if p.is_file()):
            generated.append(generate_report(target, output_name=args.output_name))
        elif target.is_dir():
            for candidate in sorted(target.iterdir()):
                if candidate.is_dir():
                    generated.append(generate_report(candidate, output_name=args.output_name))
        else:
            raise FileNotFoundError(f"Path is not a directory: {target}")

    for report in generated:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
