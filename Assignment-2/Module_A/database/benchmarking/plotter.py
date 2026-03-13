import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, cast


class Plotter:
    def __init__(self, seed: int) -> None:
        np.random.seed(seed)

    def plot_scale_size(
        self, d: int, rows: List[List[float | int | str]], range_pct: float
    ):
        bp = [r for r in rows if r[1] == "bplus"]
        br = [r for r in rows if r[1] == "brute"]
        sizes_bp = [r[0] for r in bp]
        sizes_br = [r[0] for r in br]

        ops = [
            ("insert_total_s", 2, "Total Insert Time (s)", "O(n log n)", "O(n)"),
            ("search_hit_avg_s", 3, "Avg Search-Hit Time (s)", "O(log n)", "O(n)"),
            ("search_miss_avg_s", 4, "Avg Search-Miss Time (s)", "O(log n)", "O(n)"),
            ("update_avg_s", 5, "Avg Update Time (s)", "O(log n)", "O(n)"),
            ("delete_avg_s", 6, "Avg Delete Time (s)", "O(log n)", "O(n)"),
            ("range_query_avg_s", 7, "Range Query Time (s)", "O(log n + k)", "O(n)"),
        ]

        fig, axes = plt.subplots(2, 3, figsize=(18, 10))  # type:ignore
        fig.suptitle(  # type:ignore
            f"B+ Tree (degree={d}) vs Brute Force — Size Scaling",
            fontsize=15,
        )

        for ax, (name, idx, ylabel, bp_complexity, br_complexity) in zip(
            axes.flat, ops
        ):
            # Plot empirical data
            ax.plot(
                sizes_bp,
                [r[idx] for r in bp],
                "o-",
                label="B+ Tree (empirical)",
                linewidth=2,
                color="steelblue",
            )
            ax.plot(
                sizes_br,
                [r[idx] for r in br],
                "s--",
                label="Brute Force (empirical)",
                linewidth=2,
                color="salmon",
            )

            sizes_theory = np.logspace( # type:ignore
                np.log10(min(sizes_bp + sizes_br)),
                np.log10(max(sizes_bp + sizes_br)),
                50,
            )  

            if name == "insert_total_s":
                # B+ Tree: O(n log n), Brute: O(n)
                bp_theory = sizes_theory * np.log2(sizes_theory)  # type:ignore
                br_theory = sizes_theory  # type:ignore
            elif name == "range_query_avg_s":
                # B+ Tree: O(log n + k), Brute: O(n)
                bp_theory = ( # type:ignore
                    np.log2(sizes_theory) + sizes_theory * range_pct # type:ignore
                )  
                br_theory = sizes_theory * range_pct  # type:ignore
            else:
                # Search/Update/Delete: B+ Tree O(log n), Brute: O(n)
                bp_theory = np.log2(sizes_theory)  # type:ignore
                br_theory = sizes_theory  # type:ignore

            # Normalize theory
            if len(bp) > 0 and len(br) > 0:
                bp_data = [r[idx] for r in bp]
                br_data = [r[idx] for r in br]
                bp_scale = np.median(bp_data) / np.median(bp_theory)  # type:ignore
                br_scale = np.median(br_data) / np.median(br_theory)  # type:ignore
                bp_theory = bp_theory * bp_scale  # type:ignore
                br_theory = br_theory * br_scale  # type:ignore

            ax.plot(
                sizes_theory,
                bp_theory,
                ":",
                linewidth=2.5,
                alpha=0.8,
                color="steelblue",
                label=f"B+ Tree Theory ({bp_complexity})",
            )
            ax.plot(
                sizes_theory,
                br_theory,
                ":",
                linewidth=2.5,
                alpha=0.8,
                color="salmon",
                label=f"Brute Theory ({br_complexity})",
            )

            ax.set_xlabel("N (number of rows)")
            ax.set_ylabel(ylabel)
            ax.set_title(name)
            ax.legend(fontsize=9)
            ax.set_xscale("log")
            ax.set_yscale("log")
            ax.grid(True, which="both", ls="--", alpha=0.5)
        fig.tight_layout(rect=[0, 0, 1, 0.95])  # type:ignore
        return fig

    def plot_varying_degree(self, n: int, rows: List[List[str | float | int]]):
        degs = [r[0] for r in rows]
        fig, axes = plt.subplots(1, 4, figsize=(20, 5))  # type:ignore
        fig.suptitle(f"B+ Tree - Effect of Degree (N={n})", fontsize=14)  # type:ignore

        titles = [
            "Insert Total (s)",
            "Avg Search Hit (s)",
            "Range Query (s)",
            "Avg Delete (s)",
        ]
        for i, (ax, title) in enumerate(zip(axes, titles)):
            vals = [r[i + 1] for r in rows]
            ax.bar([str(d) for d in degs], vals, color="steelblue", edgecolor="black")
            ax.set_xlabel("Degree")
            ax.set_ylabel(title)
            ax.set_title(title)
            ax.grid(axis="y", ls="--", alpha=0.5)

        fig.tight_layout(rect=[0, 0, 1, 0.93])  # type:ignore
        return fig

    def plot_key_insertion_order(
        self, n: int, deg: int, rows: List[List[str | int | float]]
    ):
        orderings = ["sequential", "random", "reverse"]
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))  # type:ignore
        fig.suptitle(  # type:ignore
            f"Key Distribution Impact (N={n}, degree={deg})", fontsize=14
        )

        x = np.arange(len(orderings))
        width = 0.35

        for ax_idx, (col_idx, title) in enumerate(
            [(2, "Insert Total (s)"), (3, "Avg Search Hit (s)")]
        ):
            bp_vals: List[int | float] = []
            br_vals: List[int | float] = []

            for d in orderings:
                for r in rows:
                    if r[0] == d and r[1] == "bplus":
                        bp_vals.append(cast(int | float, r[col_idx]))
                    if r[0] == d and r[1] == "brute":
                        br_vals.append(cast(int | float, r[col_idx]))

            ax = axes[ax_idx]
            ax.bar(x - width / 2, bp_vals, width, label="B+ Tree", color="steelblue")
            ax.bar(x + width / 2, br_vals, width, label="Brute Force", color="salmon")
            ax.set_xticks(x)
            ax.set_xticklabels(orderings)
            ax.set_ylabel(title)
            ax.set_title(title)
            ax.legend()
            ax.grid(axis="y", ls="--", alpha=0.5)

        fig.tight_layout(rect=[0, 0, 1, 0.93])  # type:ignore
        return fig
