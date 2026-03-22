import argparse
import json
from pathlib import Path


def parse_success_ratio(value: str) -> tuple[int, int]:
    if not value or "/" not in value:
        return 0, 0
    left, right = value.split("/", 1)
    try:
        return int(left), int(right)
    except ValueError:
        return 0, 0


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_comparison(before: dict, after: dict) -> list[dict]:
    rows: list[dict] = []
    common_keys = sorted(set(before.keys()) & set(after.keys()))

    for key in common_keys:
        b = before[key]
        a = after[key]

        before_avg = float(b.get("avg_ms", 0))
        after_avg = float(a.get("avg_ms", 0))
        before_max = float(b.get("max_ms", 0))
        after_max = float(a.get("max_ms", 0))

        delta_ms = before_avg - after_avg
        improvement_pct = (delta_ms / before_avg * 100.0) if before_avg > 0 else 0.0

        bs, bt = parse_success_ratio(str(b.get("success", "0/0")))
        as_, at = parse_success_ratio(str(a.get("success", "0/0")))
        before_success_pct = (bs / bt * 100.0) if bt else 0.0
        after_success_pct = (as_ / at * 100.0) if at else 0.0

        rows.append(
            {
                "endpoint": key,
                "method": a.get("method", b.get("method", "")),
                "url": a.get("url", b.get("url", "")),
                "before_avg": before_avg,
                "after_avg": after_avg,
                "before_max": before_max,
                "after_max": after_max,
                "delta_ms": delta_ms,
                "improvement_pct": improvement_pct,
                "before_success": str(b.get("success", "0/0")),
                "after_success": str(a.get("success", "0/0")),
                "before_success_pct": before_success_pct,
                "after_success_pct": after_success_pct,
            }
        )

    rows.sort(key=lambda r: r["improvement_pct"], reverse=True)
    return rows


def write_markdown(rows: list[dict], out_path: Path, before_path: Path, after_path: Path) -> None:
    improved = sum(1 for r in rows if r["delta_ms"] > 0)
    regressed = sum(1 for r in rows if r["delta_ms"] < 0)
    unchanged = len(rows) - improved - regressed

    lines: list[str] = []
    lines.append("# Profiling Comparison (Before vs After Indexing)")
    lines.append("")
    lines.append(f"- Before file: {before_path}")
    lines.append(f"- After file: {after_path}")
    lines.append(f"- Endpoints compared: {len(rows)}")
    lines.append(f"- Improved: {improved}")
    lines.append(f"- Regressed: {regressed}")
    lines.append(f"- Unchanged: {unchanged}")
    lines.append("")

    lines.append("## Top 15 Improvements")
    lines.append("")
    lines.append("| Endpoint | Before Avg (ms) | After Avg (ms) | Delta (ms) | Improvement % | Before Success | After Success |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for row in rows[:15]:
        lines.append(
            f"| {row['endpoint']} | {row['before_avg']:.2f} | {row['after_avg']:.2f} | {row['delta_ms']:.2f} | {row['improvement_pct']:.2f}% | {row['before_success']} | {row['after_success']} |"
        )
    lines.append("")

    lines.append("## Full Endpoint Comparison")
    lines.append("")
    lines.append("| Endpoint | Method | URL | Before Avg | After Avg | Delta | Improve % | Before Max | After Max |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|")
    for row in rows:
        lines.append(
            f"| {row['endpoint']} | {row['method']} | {row['url']} | {row['before_avg']:.2f} | {row['after_avg']:.2f} | {row['delta_ms']:.2f} | {row['improvement_pct']:.2f}% | {row['before_max']:.2f} | {row['after_max']:.2f} |"
        )

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare profiling JSON outputs before and after indexing")
    parser.add_argument("--before", default="profiling_results_before.json", help="Path to baseline JSON")
    parser.add_argument("--after", default="profiling_results_after.json", help="Path to indexed JSON")
    parser.add_argument(
        "--out",
        default="profiling_comparison.md",
        help="Path to markdown comparison output",
    )
    args = parser.parse_args()

    before_path = Path(args.before)
    after_path = Path(args.after)
    out_path = Path(args.out)

    before = load_json(before_path)
    after = load_json(after_path)
    rows = build_comparison(before, after)
    write_markdown(rows, out_path, before_path, after_path)

    print(f"Comparison markdown generated at: {out_path}")


if __name__ == "__main__":
    main()
