from database.table import Table
from database.benchmarking.plotter import Plotter
from typing import (
    Dict,
    Any,
    Callable,
    List,
    Literal,
    overload,
    Tuple,
    TypeVar,
    Iterable,
    cast,
)
import time
from pathlib import Path
import logging
import statistics
import random
import csv
import os
from matplotlib.figure import Figure
import tracemalloc
import numpy as np

_authors = ["jaskirat", "karan", "aarsh", "romit", "abhinav"]

T = TypeVar("T")


class PerformanceAnalyzer:
    def __init__(
        self,
        NUMROWS: List[int] = [
            100,
            200,
            400,
            800,
            1600,
            3200,
            6400,
            12800,
            25600,
            32000,
        ],
        DEGREES: List[int] = [4, 6, 8, 16, 32, 45],
        TRIALS: int = 5,
        RANGE_QUERY_PCT: float = 0.05,
        COLS: List[str] = ["id", "name", "email", "score"],
        PRIMARY_KEY: str = "id",
        RANGES_PCT: List[float] = [0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5],
        MEMORY_BENCH_SIZES:np.ndarray = np.arange(2000, 10001, 2000),
        result_folder: str | None = None,
        logfile: str = "analysis.log",
        seed: int = 230709,
    ) -> None:
        self.NUMROWS = NUMROWS
        self.DEGREES = DEGREES
        self.TRIALS = TRIALS
        self.RANGE_QUERY_PCT = RANGE_QUERY_PCT
        self.COLS = COLS
        self.PRIMARY_KEY = PRIMARY_KEY
        self.RANGES_PCT = RANGES_PCT
        self.MEMORY_BENCH_SIZES = MEMORY_BENCH_SIZES
        self.logger = logging.Logger("PerformanceAnalysisLogs")
        self.logger.setLevel(logging.INFO)
        open(Path(logfile).expanduser().resolve(strict=False), "w").close()
        file_handler = logging.FileHandler(
            Path(logfile).expanduser().resolve(strict=False)
        )
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        if result_folder is not None:
            p = Path(result_folder).expanduser().resolve(strict=False)
            if not p.exists():

                os.mkdir(result_folder)
            self.result_folder = p
        else:
            self.result_folder = None

        self.plotter = Plotter(seed)
        random.seed(seed)

    def _write_csv(
        self, filename: str, headers: List[str], rows: List[List[str | int | float]]
    ):
        if self.result_folder is not None:
            with open(self.result_folder / filename, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(headers)
                w.writerows(rows)
            self.logger.info(f"Saved to {self.result_folder}")

    def make_row(self, key: int):
        name = f"{key}_{_authors[key%len(_authors)]}"
        row: Dict[str, Any] = {
            "id": key,
            "name": name,
            "email": f"{name}@iitgn.ac.in",
            "score": key % 80,
        }
        return row

    @staticmethod
    @overload
    def timeit(
        f: Callable[..., Any], *args: ..., iter_over: None = None, **kwargs: ...
    ) -> Tuple[Any, float]: ...
    @staticmethod
    @overload
    def timeit(
        f: Callable[[T], Any], *args: ..., iter_over: Iterable[T], **kwargs: ...
    ) -> float: ...

    @staticmethod
    def timeit(
        f: Callable[..., Any],
        *args: ...,
        iter_over: Iterable[T] | None = None,
        **kwargs: ...,
    ):
        if iter_over is not None:
            s = time.perf_counter()
            for k in iter_over:
                f(k, *args, **kwargs)
            e = time.perf_counter()
            return e - s
        s = time.perf_counter()
        res = f(*args, **kwargs)
        e = time.perf_counter()
        return res, e - s

    def make_table(self, indexer: Literal["brute", "bplus"], degree: int | None = None):
        tbl = Table(
            name="bench",
            columns=self.COLS,
            primary_key=self.PRIMARY_KEY,
            indexer=indexer,
            degree=degree or self.DEGREES[0],
        )
        return tbl

    def populate_table(self, table: Table, keys: List[int]):
        for k in keys:
            table.insert_row(self.make_row(k))

    def bench_scale_size(self, d: int | None = None):
        """
        Measure insert_all, search_hit, search_miss, update, delete and range query time for brutefoce and b+tree implementation for varying number of rows, but given a fixed degree.
        """

        if d is None:
            d = self.DEGREES[0]
        self.logger.info(f"Scaling size (degree={d})")
        headers = [
            "N",
            "indexer",
            "insert_total_s",
            "search_hit_avg_s",
            "search_miss_avg_s",
            "update_avg_s",
            "delete_avg_s",
            "range_query_avg_s",
        ]
        rows: List[List[int | str | float]] = []

        for n in self.NUMROWS:
            keys: List[int] = list(range(1, n + 1))
            random.shuffle(keys)

            for indexer in ("bplus", "brute"):
                timings: Dict[str, List[float | int]] = {h: [] for h in headers[2:]}

                for _ in range(self.TRIALS):
                    tbl = self.make_table(indexer)

                    timings["insert_total_s"].append(
                        PerformanceAnalyzer.timeit(
                            lambda k: tbl.insert_row(self.make_row(k)), iter_over=keys
                        )
                    )

                    # get 10% of keys
                    hit_keys = random.sample(keys, max(1, n // 10))

                    timings["search_hit_avg_s"].append(
                        PerformanceAnalyzer.timeit(tbl.select, iter_over=hit_keys)
                    )

                    miss_keys = [n + i for i in range(1, max(2, n // 10))]
                    random.shuffle(miss_keys)

                    timings["search_miss_avg_s"].append(
                        PerformanceAnalyzer.timeit(tbl.select, iter_over=miss_keys)
                    )

                    # update 10% of keys
                    timings["update_avg_s"].append(
                        PerformanceAnalyzer.timeit(
                            lambda k: tbl.update_row(k, {"score": 2323}),
                            iter_over=hit_keys,
                        )
                    )

                    # range query
                    range_ = max(1, int(n * self.RANGE_QUERY_PCT))
                    lo = random.randint(1, max(1, n - range_))

                    timings["range_query_avg_s"].append(
                        PerformanceAnalyzer.timeit(tbl.select_range, lo, lo + range_)[1]
                    )

                    # delete
                    del_keys = random.sample(keys, max(1, n // 10))
                    timings["delete_avg_s"].append(
                        PerformanceAnalyzer.timeit(tbl.delete_row, iter_over=del_keys)
                    )

                row: List[int | str | float] = [n, indexer]
                row += [statistics.median(timings[h]) for h in headers[2:]]
                rows.append(row)
                lbl = "B+Tree" if indexer == "bplus" else "Brute"
                self.logger.info(
                    f"  N={n:>6}  {lbl}  insert={row[2]:.6f}s  "
                    f"search_hit={row[3]:.9f}s  delete={row[6]:.9f}s  "
                    f"range={row[7]:.6f}s"
                )

        self._write_csv("scale_size.csv", headers, rows)
        return self.plotter.plot_scale_size(d, rows, self.RANGE_QUERY_PCT)

    def bench_varying_degree(self, n: int = 10000):
        """
        Measuring bulk insert, avg search hit, avg range query, and avg delete time for a fixed numbe of rows, but varying the degree
        """

        # for a fixed n = 10k, vary the B+ tree degree, See trends for all operations.
        self.logger.info(f"Varying degree (N={n})")
        headers = [
            "degree",
            "insert_total_s",
            "search_hit_avg_s",
            "range_query_avg_s",
            "delete_avg_s",
        ]
        rows: List[List[int | str | float]] = []

        keys = list(range(1, n + 1))
        random.shuffle(keys)
        sample = random.sample(keys, n // 10)

        for d in self.DEGREES:
            timings: Dict[str, List[float | int]] = {h: [] for h in headers[1:]}
            for _ in range(self.TRIALS):
                tbl = self.make_table("bplus", d)

                timings["insert_total_s"].append(
                    PerformanceAnalyzer.timeit(
                        lambda k: tbl.insert_row(self.make_row(k)), iter_over=keys
                    )
                )

                timings["search_hit_avg_s"].append(
                    PerformanceAnalyzer.timeit(tbl.select, iter_over=sample)
                )

                # range query
                range_ = max(1, int(n * self.RANGE_QUERY_PCT))
                lo = random.randint(1, max(1, n - range_))

                timings["range_query_avg_s"].append(
                    PerformanceAnalyzer.timeit(tbl.select_range, lo, lo + range_)[1]
                )

                # delete
                del_keys = random.sample(keys, max(1, n // 10))
                timings["delete_avg_s"].append(
                    PerformanceAnalyzer.timeit(tbl.delete_row, iter_over=del_keys)
                    / len(del_keys)
                )

            row: List[int | str | float] = [d]
            row += [statistics.median(timings[h]) for h in headers[1:]]
            rows.append(row)
            self.logger.info(
                f"  degree={d:>3}  insert={row[1]:.4f}s  "
                f"search={row[2]:.9f}s  range={row[3]:.6f}s  "
                f"delete={row[4]:.9f}s"
            )

        self._write_csv("varying_degree.csv", headers, rows)
        return self.plotter.plot_varying_degree(n, rows)

    def bench_key_insertion_order(self, n: int = 10000, d: int | None = None):
        """compare insert + search performance for sequential, random and reverse ordered key insertion for both bplus and brute"""
        if d is None:
            d = self.DEGREES[0]
        self.logger.info(f"Key insertion order (N={n}, degree={d})")
        orderings = {
            "sequential": list(range(1, n + 1)),
            "random": random.sample(range(1, n + 1), n),
            "reverse": list(range(n, 0, -1)),
        }
        headers = ["distribution", "indexer", "insert_total_s", "search_hit_avg_s"]
        rows: List[List[str | int | float]] = []
        for order, keys in orderings.items():
            sample = random.sample(keys, n // 10)  # for searching
            for indexer in ("bplus", "brute"):
                insertion_times: List[int | float] = []
                avg_search_times: List[int | float] = []

                for _ in range(self.TRIALS):
                    tbl = self.make_table(indexer, d)

                    insertion_times.append(
                        PerformanceAnalyzer.timeit(
                            lambda k: tbl.insert_row(self.make_row(k)), iter_over=keys
                        )
                    )

                    avg_search_times.append(
                        PerformanceAnalyzer.timeit(tbl.select, iter_over=sample)
                        / len(sample)
                    )

                row: List[str | int | float] = [
                    order,
                    indexer,
                    statistics.median(insertion_times),
                    statistics.median(avg_search_times),
                ]
                rows.append(row)
                label = "B+Tree" if indexer == "bplus" else "Brute "
                self.logger.info(
                    f"  {order:>12}  {label}  insert={row[2]:.4f}s  "
                    f"search={row[3]:.9f}s"
                )
        self._write_csv("key_ordering.csv", headers, rows)
        return self.plotter.plot_key_insertion_order(n, d, rows)

    def bench_incremental_insert(self, n: int = 6000, d: int | None = None):
        """
        insert keys one by one, and see per insert latency.
        should show small spike in B+ tree, if node split happnes.
        """

        if d is None:
            d = self.DEGREES[0]
        self.logger.info(f"Incremental Insert (N={n}, degree={d})")
        keys = list(range(1, n + 1))
        random.shuffle(keys)
        res: Dict[str, List[int | float]] = {"bplus": [], "brute": []}
        for indexer in ("bplus", "brute"):
            tbl = self.make_table(indexer, d)
            for k in keys:
                res[indexer].append(
                    PerformanceAnalyzer.timeit(tbl.insert_row, self.make_row(k))[1]
                )

        rows: List[List[str | int | float]] = [
            [i + 1, res["bplus"][i], res["brute"][i]] for i in range(n)
        ]

        self._write_csv("incremental_insert.csv", ["i", "bplus_s", "brute_s"], rows)

        bp_avg = statistics.mean(res["bplus"])
        br_avg = statistics.mean(res["brute"])
        self.logger.info(
            f"B+Tree avg per-insert: {bp_avg:.9f}s\n"
            f"Brute  avg per-insert: {br_avg:.9f}s"
        )

        return self.plotter.plot_incremental_insert(n, res)

    def bench_bulk_delete(self, n: int = 10000, d: int = 4):
        """
        insert a large number of rows then delete it in random order to measure bulk delete performance.
        triggers heavy underflow/merge cascades in the B+ Tree.
        """
        self.logger.info(f"Bulk Delete (N={n}, degree={d})")
        keys = list(range(1, n + 1))
        random.shuffle(keys)
        delete = keys[:]
        random.shuffle(delete)

        headers = ["indexer", "insert_total_s", "delete_total_s"]
        rows: List[List[str | int | float]] = []

        for indexer in ("bplus", "brute"):
            insertion_time: List[int | float] = []
            deletion_time: List[int | float] = []

            for _ in range(self.TRIALS):
                tbl = self.make_table(indexer, d)

                insertion_time.append(
                    PerformanceAnalyzer.timeit(
                        lambda k: tbl.insert_row(self.make_row(k)), iter_over=keys
                    )
                )

                deletion_time.append(
                    PerformanceAnalyzer.timeit(tbl.delete_row, iter_over=delete)
                )

            row: List[str | int | float] = [
                indexer,
                statistics.median(insertion_time),
                statistics.median(deletion_time),
            ]
            rows.append(row)
            label = "B+Tree" if indexer == "bplus" else "Brute "
            self.logger.info(f"{label}  insert={row[1]:.4f}s  delete_all={row[2]:.4f}s")

        self._write_csv("bulk_delete.csv", headers, rows)
        return self.plotter.plot_bulk_delete(n, d, rows)

    def bench_range_queries(self, n: int = 10000, d: int = 4):
        """
        Do a range query, vary range span from defined low% to high% of key space. And measure times.
        """

        self.logger.info(f"Range Queries  (N={n}, degree={d})")
        headers = ["range_pct", "bplus_s", "brute_s"]
        rows: List[List[float]] = []
        keys = list(range(1, n + 1))
        random.shuffle(keys)

        for pct in self.RANGES_PCT:
            range_ = max(1, int(n * pct))
            bp_t: List[int | float] = []
            br_t: List[int | float] = []

            for _ in range(self.TRIALS):
                lo = random.randint(1, max(1, n - range_))
                hi = lo + range_

                tbl_bp = self.make_table("bplus")
                self.populate_table(tbl_bp, keys)
                bp_t.append(PerformanceAnalyzer.timeit(tbl_bp.select_range, lo, hi)[1])

                tbl_br = self.make_table("brute")
                self.populate_table(tbl_br, keys)
                br_t.append(PerformanceAnalyzer.timeit(tbl_br.select_range, lo, hi)[1])
            row = [pct, statistics.median(bp_t), statistics.median(br_t)]
            rows.append(row)
            self.logger.info(
                f"span={pct:>3}%  B+Tree={row[1]:.6f}s  Brute={row[2]:.6f}s"
            )

        self._write_csv(
            "range_queries.csv", headers, cast(List[List[int | str | float]], rows)
        )
        return self.plotter.plot_range_queries(n, d, rows)

    def bench_mixed_load(self, n: int = 10000, d: int = 4, operations: int = 10000):
        """
        Measure time for
        50% search, 20% insert, 15% update, 10% delete, 5% range query
        """
        self.logger.info(f"Mixed Workload  (N={n}, ops={operations}, degree={d})")

        headers = ["indexer", "total_s", "ops_per_sec"]
        rows: List[List[str | int | float]] = []

        keys = list(range(1, n + 1))
        random.shuffle(keys)
        next_key = n + 1

        for indexer in ("bplus", "brute"):
            times: List[float] = []
            for _ in range(self.TRIALS):
                tbl = self.make_table(indexer, d)
                self.populate_table(tbl, keys)
                available_keys = set(keys)
                nk = next_key

                t0 = time.perf_counter()
                for _ in range(operations):
                    rand = random.random()
                    match rand:
                        case _ if rand < 0.5:
                            # search
                            k = (
                                random.choice(list(available_keys))
                                if available_keys
                                else 1
                            )
                            tbl.select(k)
                        case _ if rand < 0.70:
                            # insert
                            tbl.insert_row(self.make_row(nk))
                            available_keys.add(nk)
                            nk += 1
                        case _ if rand < 0.85:
                            # update
                            if available_keys:
                                k = random.choice(list(available_keys))
                                tbl.update_row(k, {"score": 42})
                        case _ if rand < 0.95:
                            # delete
                            if available_keys:
                                k = random.choice(list(available_keys))
                                tbl.delete_row(k)
                                available_keys.discard(k)
                        case _:
                            # range query
                            lo = random.randint(1, max(1, nk - 500))
                            tbl.select_range(lo, lo + 500)
                times.append(time.perf_counter() - t0)

            med = statistics.median(times)
            row: List[str | float | int] = [indexer, med, operations / med]
            rows.append(row)
            label = "B+Tree" if indexer == "bplus" else "Brute "
            self.logger.info(
                f"{label}  total={med:.4f}s  throughput={operations / med:.0f} ops/s"
            )

        self._write_csv("mixed_load.csv", headers, rows)
        return self.plotter.plot_mixed_load(n, d, operations, rows)

    def bench_memory_usage(self, sizes: List[int] | None = None):
        """
        Measure the peak memory usage scaling with the number of rows across varying degrees.
        """
        if sizes is None:
            sizes = self.MEMORY_BENCH_SIZES
            
        self.logger.info(f"Memory Usage Scaling (sizes={sizes}, degrees={self.DEGREES})")
        
        headers = ["N", "indexer", "degree", "peak_memory_mb"]
        rows: List[List[int | str | float]] = []

        for n in sizes:
            keys = list(range(1, n + 1))
            random.shuffle(keys)

            tracemalloc.start()
            tbl_brute = self.make_table("brute")
            for k in keys:
                tbl_brute.insert_row(self.make_row(k))
            
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            peak_mb = peak / (1024 * 1024)
            rows.append([n, "brute", 0, peak_mb]) 
            self.logger.info(f"  N={n:>6}  Brute Force    peak_mem={peak_mb:.4f}MB")

            # 2. Test B+ Tree across all configured degrees
            for d in self.DEGREES:
                tracemalloc.start()
                tbl_bp = self.make_table("bplus", d)
                for k in keys:
                    tbl_bp.insert_row(self.make_row(k))
                
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                
                peak_mb = peak / (1024 * 1024)
                rows.append([n, "bplus", d, peak_mb])
                self.logger.info(f"  N={n:>6}  B+Tree (d={d:<2}) peak_mem={peak_mb:.4f}MB")

        self._write_csv("memory_usage.csv", headers, rows)
        
        return self.plotter.plot_memory_usage(rows) 


    def run(self):
        figs: Dict[str, Tuple[str, Figure]] = {}
        for i in PerformanceAnalyzer.__dict__.keys():
            if i.startswith("bench_"):
                print(f"Running {i}")
                f = PerformanceAnalyzer.__dict__[i]
                figs[i] = (" ".join(map(str.strip, f.__doc__.split("\n"))), f(self))
        return figs
