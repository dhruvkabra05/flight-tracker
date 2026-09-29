import time


def linear_search(records, target):
    start = time.perf_counter()
    comparisons = 0
    for record in records:
        comparisons += 1
        if str(record.get("passenger_id", "")).lower() == str(target).lower():
            return {"found": True, "record": record, "comparisons": comparisons,
                    "time_ms": round((time.perf_counter() - start) * 1000, 5)}
    return {"found": False, "record": None, "comparisons": comparisons,
            "time_ms": round((time.perf_counter() - start) * 1000, 5)}


def binary_search(records, target):
    start = time.perf_counter()
    # The caller supplies data already sorted by numeric passenger_id.
    low, high = 0, len(records) - 1
    comparisons = 0
    try:
        target_num = int(target)
    except (TypeError, ValueError):
        return {"found": False, "record": None, "comparisons": 0,
                "time_ms": round((time.perf_counter() - start) * 1000, 5)}
    while low <= high:
        mid = (low + high) // 2
        comparisons += 1
        try:
            value = int(records[mid]["passenger_id"])
        except (TypeError, ValueError):
            value = 0
        if value == target_num:
            return {"found": True, "record": records[mid], "comparisons": comparisons,
                    "time_ms": round((time.perf_counter() - start) * 1000, 5)}
        if value < target_num:
            low = mid + 1
        else:
            high = mid - 1
    return {"found": False, "record": None, "comparisons": comparisons,
            "time_ms": round((time.perf_counter() - start) * 1000, 5)}
