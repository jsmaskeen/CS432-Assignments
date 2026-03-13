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

            sizes_theory = np.logspace(  # type:ignore
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
                bp_theory = (  # type:ignore
                    np.log2(sizes_theory) + sizes_theory * range_pct  # type:ignore
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

    def plot_incremental_insert(self, n: int, res: Dict[str, List[int | float]]):
        fig, (ax1, ax2) = plt.subplots(  # type:ignore
            2, 1, figsize=(14, 8), sharex=True
        )
        fig.suptitle(f"Per-Insert Latency (N={n})", fontsize=14)  # type:ignore

        xs = range(1, n + 1)
        window = 50  # moving avg

        for ax, indexer, color, title, complexity in [
            (ax1, "bplus", "steelblue", "B+ Tree", "O(log n)"),
            (ax2, "brute", "salmon", "Brute Force", "O(1)"),
        ]:
            raw = res[indexer]
            ax.plot(xs, raw, alpha=0.15, color=color, linewidth=0.5)
            ma = np.convolve(raw, np.ones(window) / window, mode="valid")
            ax.plot(
                range(window, n + 1),
                ma,
                color=color,
                linewidth=1.5,
                label=f"MA-{window} (empirical)",
            )

            if indexer == "bplus":
                # B+ Tree: O(log n) per insert
                theory = np.log2(np.arange(1, n + 1))
            else:
                # Brute: O(1) per insert
                theory = np.ones(n)

            theory_scale = np.median(ma) / np.median(theory)
            theory = theory * theory_scale

            ax.plot(
                xs,
                theory,
                ":",
                linewidth=2.5,
                alpha=0.8,
                color=color,
                label=f"Theory ({complexity})",
            )
            ax.set_yscale("log")
            ax.set_ylabel("Time per insert (s)")
            ax.set_title(title)
            ax.legend()
            ax.grid(True, ls="--", alpha=0.5)

        ax2.set_xlabel("Insert #")
        fig.tight_layout(rect=[0, 0, 1, 0.95])  # type:ignore

        return fig

    def plot_bulk_delete(self, n: int, d: int, rows: List[List[str | int | float]]):
        labels = ["B+ Tree", "Brute Force"]
        insert_vals = [r[1] for r in rows]
        delete_vals = [r[2] for r in rows]

        x = np.arange(len(labels))
        width = 0.35
        fig, ax = plt.subplots(figsize=(8, 5))  # type:ignore
        ax.bar(  # type:ignore
            x - width / 2, insert_vals, width, label="Insert All", color="steelblue"
        )
        ax.bar(  # type:ignore
            x + width / 2, delete_vals, width, label="Delete All", color="salmon"
        )
        ax.set_xticks(x)  # type:ignore
        ax.set_xticklabels(labels)  # type:ignore
        ax.set_ylabel("Time (s)")  # type:ignore
        ax.set_title(f"Bulk Insert + Delete Test (N={n}, degree={d})")  # type:ignore
        ax.legend()  # type:ignore
        ax.grid(axis="y", ls="--", alpha=0.5)  # type:ignore
        fig.tight_layout()  # type:ignore
        return fig

    def plot_range_queries(self, n: int, d: int, rows: List[List[float]]):
        pcts = [r[0] for r in rows]
        bp_t = [r[1] for r in rows]
        br_t = [r[2] for r in rows]

        fig, ax = plt.subplots(figsize=(10, 5))  # type: ignore
        ax.plot(pcts, bp_t, "o-", label="B+ Tree (empirical)", linewidth=2, color="steelblue")  # type: ignore
        ax.plot(pcts, br_t, "s--", label="Brute Force (empirical)", linewidth=2, color="salmon")  # type: ignore

        # B+ Tree:
        # O(log n) to find starting leaf position
        # O(k) to traverse linked list and collect k results
        # Total: O(log n + k) for range queries
        # Brute Force: O(n), must scan entire unordered list regardless of range size
        pcts_theory = np.linspace(min(pcts), max(pcts), 50)
        k_results = n * pcts_theory
        bp_theory = np.log2(n) + k_results
        br_theory = np.ones_like(pcts_theory) * n

        # Normalize
        if len(bp_t) > 0:
            bp_scale = np.median(bp_t) / np.median(bp_theory)
            bp_theory = bp_theory * bp_scale

        if len(br_t) > 0:
            br_scale = np.median(br_t) / np.median(br_theory)
            br_theory = br_theory * br_scale

        ax.plot(pcts_theory, bp_theory, ":", linewidth=2.5, alpha=0.8, color="steelblue", label="B+ Tree Theory (O(log n + k) via linked list)")  # type: ignore
        ax.plot(pcts_theory, br_theory, ":", linewidth=2.5, alpha=0.8, color="salmon", label="Brute Theory (O(n))")  # type: ignore

        ax.set_xlabel("Range Span (% of key space)")  # type: ignore
        ax.set_ylabel("Query Time (s)")  # type: ignore
        ax.set_title(f"Range Query Scaling (N={n}, Degree={d})")  # type: ignore
        ax.legend()  # type: ignore
        ax.grid(True, ls="--", alpha=0.5)  # type: ignore
        fig.tight_layout()
        return fig

    def plot_mixed_load(
        self, n: int, d: int, operations: int, rows: List[List[str | int | float]]
    ):
        labels = ["B+ Tree", "Brute Force"]
        throughput = [r[2] for r in rows]

        fig, ax = plt.subplots(figsize=(8, 5))  # type:ignore
        ax.bar(# type:ignore
            labels, throughput, color=["steelblue", "salmon"], edgecolor="black"
        )  
        ax.set_ylabel("Throughput (ops/s)")  # type:ignore
        ax.set_title(# type:ignore
            f"Mixed Workload Throughput (N={n}, Degree={d}, Operations={operations} ops)"
        )  
        ax.grid(axis="y", ls="--", alpha=0.5)  # type:ignore
        fig.tight_layout()
        return fig
