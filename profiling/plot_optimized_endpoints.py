import argparse
import json
from pathlib import Path


OPTIMIZED_ENDPOINTS = [
    {
        "name": "rides :: GET /api/v1/rides",
        "label": "rides:list",
        "sql_before": "SELECT * FROM Rides WHERE Ride_Status = 'Open' ORDER BY Departure_Time ASC LIMIT :limit;",
        "sql_after": "SELECT * FROM Rides WHERE Ride_Status = 'Open' ORDER BY Departure_Time ASC LIMIT :limit;",
        "indexes": ["idx_rides_status_departure_time (Ride_Status, Departure_Time)"],
    },
    {
        "name": "admin :: GET /api/v1/admin/rides/open",
        "label": "admin:rides_open",
        "sql_before": "SELECT * FROM Rides WHERE Ride_Status = 'Open' ORDER BY Departure_Time ASC;",
        "sql_after": "SELECT * FROM Rides WHERE Ride_Status = 'Open' ORDER BY Departure_Time ASC;",
        "indexes": ["idx_rides_status_departure_time (Ride_Status, Departure_Time)"],
    },
    {
        "name": "admin :: GET /api/v1/admin/rides/completed",
        "label": "admin:rides_completed",
        "sql_before": "SELECT * FROM Rides WHERE Ride_Status = 'Completed' ORDER BY Departure_Time DESC;",
        "sql_after": "SELECT * FROM Rides WHERE Ride_Status = 'Completed' ORDER BY Departure_Time DESC;",
        "indexes": ["idx_rides_status_departure_time (Ride_Status, Departure_Time)"],
    },
    {
        "name": "admin :: GET /api/v1/admin/rides/active",
        "label": "admin:rides_active",
        "sql_before": "SELECT * FROM Rides WHERE Ride_Status = 'Started' ORDER BY Departure_Time ASC;",
        "sql_after": "SELECT * FROM Rides WHERE Ride_Status = 'Started' ORDER BY Departure_Time ASC;",
        "indexes": ["idx_rides_status_departure_time (Ride_Status, Departure_Time)"],
    },
    {
        "name": "bookings :: GET /api/v1/rides/my/bookings",
        "label": "bookings:my",
        "sql_before": "SELECT * FROM Bookings WHERE Passenger_MemberID = :member_id ORDER BY Booked_At DESC;",
        "sql_after": "SELECT * FROM Bookings WHERE Passenger_MemberID = :member_id ORDER BY Booked_At DESC;",
        "indexes": ["idx_bookings_passenger_booked_at (Passenger_MemberID, Booked_At)"],
    },
    {
        "name": "bookings :: GET /api/v1/rides/{ride_id}/bookings/pending",
        "label": "bookings:pending",
        "sql_before": "SELECT * FROM Bookings WHERE RideID = :ride_id AND Booking_Status = 'Pending' ORDER BY Booked_At DESC;",
        "sql_after": "SELECT * FROM Bookings WHERE RideID = :ride_id AND Booking_Status = 'Pending' ORDER BY Booked_At DESC;",
        "indexes": ["idx_bookings_ride_status_booked_at (RideID, Booking_Status, Booked_At)"],
    },
    {
        "name": "reviews :: GET /api/v1/reviews/ride/{ride_id}",
        "label": "reviews:ride",
        "sql_before": "SELECT * FROM Reputation_Reviews WHERE RideID = :ride_id ORDER BY Created_At DESC;",
        "sql_after": "SELECT * FROM Reputation_Reviews WHERE RideID = :ride_id ORDER BY Created_At DESC;",
        "indexes": ["idx_reviews_ride_created_at (RideID, Created_At)"],
    },
    {
        "name": "reviews :: GET /api/v1/reviews/member/{member_id}",
        "label": "reviews:member",
        "sql_before": "SELECT * FROM Reputation_Reviews WHERE Reviewer_MemberID = :member_id OR Reviewee_MemberID = :member_id ORDER BY Created_At DESC;",
        "sql_after": "SELECT * FROM Reputation_Reviews WHERE Reviewer_MemberID = :member_id OR Reviewee_MemberID = :member_id ORDER BY Created_At DESC;",
        "indexes": [
            "idx_reviews_reviewer_created_at (Reviewer_MemberID, Created_At)",
            "idx_reviews_reviewee_created_at (Reviewee_MemberID, Created_At)",
        ],
    },
    {
        "name": "reviews :: GET /api/v1/reviews/my",
        "label": "reviews:my",
        "sql_before": "SELECT * FROM Reputation_Reviews WHERE Reviewer_MemberID = :member_id ORDER BY Created_At DESC;",
        "sql_after": "SELECT * FROM Reputation_Reviews WHERE Reviewer_MemberID = :member_id ORDER BY Created_At DESC;",
        "indexes": ["idx_reviews_reviewer_created_at (Reviewer_MemberID, Created_At)"],
    },
    {
        "name": "settlements :: GET /api/v1/settlements/my",
        "label": "settlements:my",
        "sql_before": "SELECT cs.* FROM Cost_Settlements cs JOIN Bookings b ON b.BookingID = cs.BookingID JOIN Rides r ON r.RideID = b.RideID WHERE b.Passenger_MemberID = :member_id OR r.Host_MemberID = :member_id ORDER BY cs.SettlementID DESC;",
        "sql_after": "SELECT cs.* FROM Cost_Settlements cs JOIN Bookings b ON b.BookingID = cs.BookingID JOIN Rides r ON r.RideID = b.RideID WHERE b.Passenger_MemberID = :member_id OR r.Host_MemberID = :member_id ORDER BY cs.SettlementID DESC;",
        "indexes": [
            "idx_bookings_passenger_booked_at (Passenger_MemberID, Booked_At)",
            "idx_rides_host_ride_id (Host_MemberID, RideID)",
            "idx_settlements_settlement_booking (SettlementID, BookingID)",
        ],
    },
]


def load_results(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_rows(before: dict, after: dict) -> list[dict]:
    rows: list[dict] = []
    for item in OPTIMIZED_ENDPOINTS:
        endpoint = item["name"]
        if endpoint not in before or endpoint not in after:
            continue

        before_avg = float(before[endpoint].get("avg_ms", 0))
        after_avg = float(after[endpoint].get("avg_ms", 0))
        delta = before_avg - after_avg
        improvement_pct = (delta / before_avg * 100.0) if before_avg > 0 else 0.0

        rows.append(
            {
                "endpoint": endpoint,
                "label": item["label"],
                "before_avg": before_avg,
                "after_avg": after_avg,
                "delta": delta,
                "improvement_pct": improvement_pct,
                "sql_before": item["sql_before"],
                "sql_after": item["sql_after"],
                "indexes": item["indexes"],
            }
        )

    return rows


def write_sql_markdown(rows: list[dict], out_md: Path) -> None:
    lines: list[str] = []
    lines.append("# Optimized Endpoints: SQL Before vs After Indexing")
    lines.append("")
    lines.append("These are the endpoints intentionally targeted by the plug-in index set.")
    lines.append("The API SQL statements are the same before/after; performance changes come from index availability and query plan changes.")
    lines.append("")

    lines.append("| Endpoint | Before Avg (ms) | After Avg (ms) | Delta (ms) | Improvement % |")
    lines.append("|---|---:|---:|---:|---:|")
    for row in rows:
        lines.append(
            f"| {row['endpoint']} | {row['before_avg']:.2f} | {row['after_avg']:.2f} | {row['delta']:.2f} | {row['improvement_pct']:.2f}% |"
        )

    lines.append("")
    for row in rows:
        lines.append(f"## {row['endpoint']}")
        lines.append("")
        lines.append("**SQL (Before Indexing):**")
        lines.append("")
        lines.append("```sql")
        lines.append(row["sql_before"])
        lines.append("```")
        lines.append("")
        lines.append("**SQL (After Indexing):**")
        lines.append("")
        lines.append("```sql")
        lines.append(row["sql_after"])
        lines.append("```")
        lines.append("")
        lines.append("**Relevant Indexes:**")
        lines.append("")
        for idx in row["indexes"]:
            lines.append(f"- {idx}")
        lines.append("")

    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_plot(rows: list[dict], out_png: Path) -> None:
    try:
        plt = __import__("matplotlib.pyplot", fromlist=["pyplot"])
    except ImportError as exc:
        raise SystemExit(
            "matplotlib is not installed. Install it with: pip install matplotlib"
        ) from exc

    labels = [row["label"] for row in rows]
    before_vals = [row["before_avg"] for row in rows]
    after_vals = [row["after_avg"] for row in rows]

    x = list(range(len(rows)))
    width = 0.38

    fig, ax = plt.subplots(figsize=(max(12, len(rows) * 1.3), 7.5))
    bars_before = ax.bar([i - width / 2 for i in x], before_vals, width=width, label="Before Indexing")
    bars_after = ax.bar([i + width / 2 for i in x], after_vals, width=width, label="After Indexing")

    ax.set_title("Optimized Endpoints: Before vs After Indexing (Avg Latency)")
    ax.set_xlabel("Endpoints")
    ax.set_ylabel("Average Latency (ms)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=40, ha="right")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.35)

    for bar in bars_before:
        h = bar.get_height()
        ax.annotate(f"{h:.1f}", (bar.get_x() + bar.get_width() / 2, h),
                    textcoords="offset points", xytext=(0, 4), ha="center", fontsize=8)
    for bar in bars_after:
        h = bar.get_height()
        ax.annotate(f"{h:.1f}", (bar.get_x() + bar.get_width() / 2, h),
                    textcoords="offset points", xytext=(0, 4), ha="center", fontsize=8)

    for i, row in enumerate(rows):
        top = max(before_vals[i], after_vals[i])
        ax.annotate(
            f"{row['improvement_pct']:.1f}%",
            (i, top),
            textcoords="offset points",
            xytext=(0, 18),
            ha="center",
            fontsize=8,
            color="green" if row["improvement_pct"] >= 0 else "crimson",
            fontweight="bold",
        )

    fig.tight_layout()
    fig.savefig(out_png, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot and document optimized endpoint latencies before/after indexing")
    parser.add_argument("--before", default="profiling_results_before.json", help="Before-indexing JSON")
    parser.add_argument("--after", default="profiling_results_after.json", help="After-indexing JSON")
    parser.add_argument("--plot", default="optimized_endpoints_latency_barplot.png", help="Output PNG path")
    parser.add_argument("--sql-md", default="optimized_endpoints_sql_before_after.md", help="Output markdown path")
    args = parser.parse_args()

    before = load_results(Path(args.before))
    after = load_results(Path(args.after))
    rows = build_rows(before, after)

    if not rows:
        raise SystemExit("No optimized endpoints found in both files.")

    make_plot(rows, Path(args.plot))
    write_sql_markdown(rows, Path(args.sql_md))

    print(f"Saved bar plot: {args.plot}")
    print(f"Saved SQL markdown: {args.sql_md}")


if __name__ == "__main__":
    main()
