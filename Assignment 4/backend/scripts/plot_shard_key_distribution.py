from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt


def _resolve_path(base_dir: Path, user_path: str) -> Path:
    path = Path(user_path)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot shard distribution per shard-key candidate policy")
    parser.add_argument(
        "--input",
        default="shard_key_entropy_comparison.json",
        help="Input JSON path (relative to backend/scripts or absolute)",
    )
    parser.add_argument(
        "--output",
        default="../../images/shard_key_policy_distribution.png",
        help="Output image path (relative to backend/scripts or absolute)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=7,
        help="Number of top candidates to include in the chart",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    input_path = _resolve_path(script_dir, args.input)
    output_path = _resolve_path(script_dir, args.output)

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    ranked = payload.get("ranked_candidates", [])[: max(1, args.top)]
    if not ranked:
        raise RuntimeError("No ranked_candidates found in input JSON")

    labels = [str(item["candidate"]).replace("_", "\n") for item in ranked]
    shard0 = [int(item["counts_by_shard"].get("0", 0)) for item in ranked]
    shard1 = [int(item["counts_by_shard"].get("1", 0)) for item in ranked]
    shard2 = [int(item["counts_by_shard"].get("2", 0)) for item in ranked]

    x = list(range(len(labels)))
    width = 0.24

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(14, 8))
    fig.patch.set_facecolor("#111418")
    ax.set_facecolor("#111418")

    ax.bar([value - width for value in x], shard0, width, label="Shard 0", color="#5b57c9")
    ax.bar(x, shard1, width, label="Shard 1", color="#57b589")
    ax.bar([value + width for value in x], shard2, width, label="Shard 2", color="#d06a43")

    ax.set_title("Shard Distribution by Candidate Shard-Key Policy", fontsize=16, pad=14)
    ax.set_ylabel("Ride Count")
    ax.set_xlabel("Candidate Policy")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.grid(axis="y", color="#2a2f38", linestyle="-", linewidth=0.8, alpha=0.8)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, ncols=3, loc="upper left")

    top = payload.get("recommended_shard_key", {})
    subtitle = (
        f"Recommended: {top.get('candidate', 'n/a')} ({top.get('method', 'n/a')}), "
        f"normalized entropy={float(top.get('normalized_entropy', 0.0)):.4f}"
    )
    ax.text(0.0, 1.02, subtitle, transform=ax.transAxes, fontsize=11, color="#d7dde8")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight")

    print(f"Saved plot to: {output_path}")


if __name__ == "__main__":
    main()
