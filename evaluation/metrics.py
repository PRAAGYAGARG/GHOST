import math


def compute_metrics(results):
    total = len(results)
    available_results = [r for r in results if r.get("available", False)]
    available_count = len(available_results)

    errors = [
        r["location_error"]
        for r in available_results
        if r.get("location_error") is not None
    ]

    if not errors:
        return {
            "total_reports": total,
            "available_reports": 0,
            "availability": 0.0,
            "avg_location_error": None,
            "max_location_error": None,
            "p95_location_error": None,
            "median_location_error": None,
            "std_location_error": None,
        }

    errors_sorted = sorted(errors)
    n = len(errors_sorted)
    avg_err = sum(errors) / n
    variance = sum((e - avg_err) ** 2 for e in errors) / max(n - 1, 1)
    std_err = math.sqrt(variance)

    p95_idx = min(int(math.ceil(0.95 * n)) - 1, n - 1)
    median_idx = n // 2

    return {
        "total_reports": total,
        "available_reports": available_count,
        "availability": round(available_count / max(total, 1), 4),
        "avg_location_error": round(avg_err, 2),
        "max_location_error": round(max(errors), 2),
        "p95_location_error": round(errors_sorted[p95_idx], 2),
        "median_location_error": round(errors_sorted[median_idx], 2),
        "std_location_error": round(std_err, 2),
    }


def compute_multi_snapshot_metrics(all_results):
    flat = []
    for snapshot_results in all_results:
        flat.extend(snapshot_results)
    return compute_metrics(flat)
