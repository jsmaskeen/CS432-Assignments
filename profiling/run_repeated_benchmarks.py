import argparse
import json
import os
import shutil
import statistics
import subprocess
from pathlib import Path
from typing import Any


def run_cmd(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> None:
    effective_cmd = cmd
    if cmd and cmd[0].endswith(".sh"):
        effective_cmd = ["bash", *cmd]

    print(f"[cmd] ({cwd}) {' '.join(effective_cmd)}")
    result = subprocess.run(effective_cmd, cwd=str(cwd), env=env, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}) in {cwd}: {' '.join(effective_cmd)}"
        )


def load_env_file(env_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not env_path.exists():
        return values

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def parse_success_ratio(value: str) -> float:
    if "/" not in value:
        return 0.0
    left, right = value.split("/", 1)
    try:
        num = int(left)
        den = int(right)
        return (num / den * 100.0) if den > 0 else 0.0
    except ValueError:
        return 0.0


def aggregate_results(json_files: list[Path]) -> dict[str, dict[str, Any]]:
    by_endpoint: dict[str, list[dict[str, Any]]] = {}

    for path in json_files:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        for endpoint, metrics in payload.items():
            by_endpoint.setdefault(endpoint, []).append(metrics)

    aggregated: dict[str, dict[str, Any]] = {}
    for endpoint, rows in by_endpoint.items():
        avg_values = [float(item.get("avg_ms", 0.0)) for item in rows]
        max_values = [float(item.get("max_ms", 0.0)) for item in rows]
        success_values = [parse_success_ratio(str(item.get("success", "0/0"))) for item in rows]

        avg_mean = statistics.mean(avg_values) if avg_values else 0.0
        avg_std = statistics.pstdev(avg_values) if len(avg_values) > 1 else 0.0
        max_mean = statistics.mean(max_values) if max_values else 0.0
        max_std = statistics.pstdev(max_values) if len(max_values) > 1 else 0.0
        success_mean = statistics.mean(success_values) if success_values else 0.0

        aggregated[endpoint] = {
            "method": rows[0].get("method", ""),
            "url": rows[0].get("url", ""),
            "runs": len(rows),
            "avg_ms_mean": avg_mean,
            "avg_ms_std": avg_std,
            "max_ms_mean": max_mean,
            "max_ms_std": max_std,
            "success_pct_mean": success_mean,
        }

    return aggregated


def compare_aggregates(before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    keys = sorted(set(before.keys()) & set(after.keys()))

    for endpoint in keys:
        b = before[endpoint]
        a = after[endpoint]

        before_avg = float(b["avg_ms_mean"])
        after_avg = float(a["avg_ms_mean"])
        delta = before_avg - after_avg
        improvement_pct = (delta / before_avg * 100.0) if before_avg > 0 else 0.0

        rows.append(
            {
                "endpoint": endpoint,
                "method": a["method"],
                "url": a["url"],
                "before_avg_mean": before_avg,
                "before_avg_std": float(b["avg_ms_std"]),
                "after_avg_mean": after_avg,
                "after_avg_std": float(a["avg_ms_std"]),
                "delta_ms": delta,
                "improvement_pct": improvement_pct,
                "before_success_pct": float(b["success_pct_mean"]),
                "after_success_pct": float(a["success_pct_mean"]),
            }
        )

    rows.sort(key=lambda x: x["improvement_pct"], reverse=True)
    return rows


def write_markdown(out_path: Path, comparison_rows: list[dict[str, Any]], runs: int) -> None:
    improved = sum(1 for r in comparison_rows if r["delta_ms"] > 0)
    regressed = sum(1 for r in comparison_rows if r["delta_ms"] < 0)
    unchanged = len(comparison_rows) - improved - regressed

    lines: list[str] = []
    lines.append("# Repeated Benchmark Comparison (Before vs After Indexing)")
    lines.append("")
    lines.append(f"- Repetitions per mode: {runs}")
    lines.append(f"- Endpoints compared: {len(comparison_rows)}")
    lines.append(f"- Improved: {improved}")
    lines.append(f"- Regressed: {regressed}")
    lines.append(f"- Unchanged: {unchanged}")
    lines.append("")

    lines.append("## Top 20 Improvements (mean avg latency)")
    lines.append("")
    lines.append("| Endpoint | Before mean±std (ms) | After mean±std (ms) | Delta (ms) | Improve % | Before success % | After success % |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for row in comparison_rows[:20]:
        lines.append(
            f"| {row['endpoint']} | {row['before_avg_mean']:.2f}±{row['before_avg_std']:.2f} | {row['after_avg_mean']:.2f}±{row['after_avg_std']:.2f} | {row['delta_ms']:.2f} | {row['improvement_pct']:.2f}% | {row['before_success_pct']:.1f}% | {row['after_success_pct']:.1f}% |"
        )
    lines.append("")

    lines.append("## Full Comparison")
    lines.append("")
    lines.append("| Endpoint | Method | URL | Before mean | After mean | Delta | Improve % |")
    lines.append("|---|---|---|---:|---:|---:|---:|")
    for row in comparison_rows:
        lines.append(
            f"| {row['endpoint']} | {row['method']} | {row['url']} | {row['before_avg_mean']:.2f} | {row['after_avg_mean']:.2f} | {row['delta_ms']:.2f} | {row['improvement_pct']:.2f}% |"
        )

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_mode(
    mode: str,
    runs: int,
    workspace_root: Path,
    profiling_dir: Path,
    backend_dir: Path,
    mysql_user: str,
    mysql_password: str,
    mysql_db: str,
    apply_indexes_sql: Path,
    out_raw_dir: Path,
) -> list[Path]:
    out_files: list[Path] = []

    for run_number in range(1, runs + 1):
        print(f"\n===== {mode.upper()} run {run_number}/{runs} =====")

        run_cmd(["./clean_database.sh"], workspace_root)
        run_cmd(["python3", "seed_db_massive.py"], backend_dir)

        if mode == "after":
            mysql_env = os.environ.copy()
            mysql_env["MYSQL_PWD"] = mysql_password
            apply_source = apply_indexes_sql
            try:
                apply_source = apply_indexes_sql.relative_to(workspace_root)
            except ValueError:
                pass
            run_cmd(
                [
                    "mysql",
                    f"-u{mysql_user}",
                    mysql_db,
                    "-e",
                    f"source {apply_source}",
                ],
                workspace_root,
                env=mysql_env,
            )

        run_cmd(["python3", "profile_apis.py"], profiling_dir)

        src = profiling_dir / "profiling_results.json"
        dst = out_raw_dir / f"{mode}_run_{run_number}.json"
        shutil.copy2(src, dst)
        out_files.append(dst)
        print(f"Saved: {dst}")

    return out_files


def main() -> None:
    parser = argparse.ArgumentParser(description="Run repeated before/after profiling experiments and aggregate results")
    parser.add_argument("--runs", type=int, default=5, help="Number of repetitions per mode")
    parser.add_argument("--workspace-root", default=".")
    parser.add_argument("--mysql-user", default=None)
    parser.add_argument("--mysql-password", default=None)
    parser.add_argument("--mysql-db", default="cabSharing")
    parser.add_argument("--indexes-apply", default="profiling/indexes_apply.sql")
    parser.add_argument("--out-dir", default="profiling/repeated_runs")
    parser.add_argument("--out-summary-json", default="profiling/repeated_comparison.json")
    parser.add_argument("--out-summary-md", default="profiling/repeated_comparison.md")
    args = parser.parse_args()

    workspace_root = Path(args.workspace_root).resolve()
    if workspace_root.name == "profiling":
        workspace_root = workspace_root.parent

    profiling_dir = workspace_root / "profiling"
    backend_dir = workspace_root / "backend"
    apply_indexes_sql = (workspace_root / args.indexes_apply).resolve()

    env_values = load_env_file(backend_dir / ".env")
    mysql_user = args.mysql_user or env_values.get("MYSQL_USER") or "root"
    mysql_password = args.mysql_password or env_values.get("MYSQL_PASSWORD") or ""
    mysql_db = args.mysql_db or "cabSharing"

    out_dir = (workspace_root / args.out_dir).resolve()
    out_raw_dir = out_dir / "raw"
    out_raw_dir.mkdir(parents=True, exist_ok=True)

    before_files = run_mode(
        mode="before",
        runs=args.runs,
        workspace_root=workspace_root,
        profiling_dir=profiling_dir,
        backend_dir=backend_dir,
        mysql_user=mysql_user,
        mysql_password=mysql_password,
        mysql_db=mysql_db,
        apply_indexes_sql=apply_indexes_sql,
        out_raw_dir=out_raw_dir,
    )

    after_files = run_mode(
        mode="after",
        runs=args.runs,
        workspace_root=workspace_root,
        profiling_dir=profiling_dir,
        backend_dir=backend_dir,
        mysql_user=mysql_user,
        mysql_password=mysql_password,
        mysql_db=mysql_db,
        apply_indexes_sql=apply_indexes_sql,
        out_raw_dir=out_raw_dir,
    )

    before_agg = aggregate_results(before_files)
    after_agg = aggregate_results(after_files)
    comparison = compare_aggregates(before_agg, after_agg)

    out_summary_json = (workspace_root / args.out_summary_json).resolve()
    out_summary_md = (workspace_root / args.out_summary_md).resolve()

    payload = {
        "runs": args.runs,
        "before_files": [str(p.relative_to(workspace_root)) for p in before_files],
        "after_files": [str(p.relative_to(workspace_root)) for p in after_files],
        "before_aggregate": before_agg,
        "after_aggregate": after_agg,
        "comparison": comparison,
    }

    out_summary_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(out_summary_md, comparison, args.runs)

    print(f"\nSaved aggregate JSON: {out_summary_json}")
    print(f"Saved aggregate markdown: {out_summary_md}")


if __name__ == "__main__":
    main()
