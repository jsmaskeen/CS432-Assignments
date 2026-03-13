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