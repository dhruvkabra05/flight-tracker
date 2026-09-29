import time


def value_for(record, key):
    value = record.get(key, "")
    if key in {"passenger_id", "priority", "boarding_group"}:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
    return str(value).lower()


def compare(a, b, key, descending=False, metrics=None):
    if metrics is not None:
        metrics["comparisons"] += 1
    av, bv = value_for(a, key), value_for(b, key)
    result = (av > bv) - (av < bv)
    return -result if descending else result


def swap(arr, i, j, metrics):
    if i != j:
        arr[i], arr[j] = arr[j], arr[i]
        metrics["swaps"] += 1


def quick_sort(records, key="priority", descending=False):
    arr = [dict(r) for r in records]
    metrics = {"comparisons": 0, "swaps": 0}

    def partition(low, high):
        pivot = arr[high]
        i = low - 1
        for j in range(low, high):
            if compare(arr[j], pivot, key, descending, metrics) <= 0:
                i += 1
                swap(arr, i, j, metrics)
        swap(arr, i + 1, high, metrics)
        return i + 1

    start = time.perf_counter()
    def sort(low, high):
        if low < high:
            p = partition(low, high)
            sort(low, p - 1)
            sort(p + 1, high)
    sort(0, len(arr) - 1)
    metrics["time_ms"] = round((time.perf_counter() - start) * 1000, 5)
    return arr, metrics


def merge_sort(records, key="priority", descending=False):
    arr = [dict(r) for r in records]
    metrics = {"comparisons": 0, "swaps": 0}

    def merge(left, right):
        result = []
        i = j = 0
        while i < len(left) and j < len(right):
            if compare(left[i], right[j], key, descending, metrics) <= 0:
                result.append(left[i]); i += 1
            else:
                result.append(right[j]); j += 1
        return result + left[i:] + right[j:]

    start = time.perf_counter()
    def sort(items):
        if len(items) <= 1:
            return items
        mid = len(items) // 2
        return merge(sort(items[:mid]), sort(items[mid:]))
    arr = sort(arr)
    metrics["time_ms"] = round((time.perf_counter() - start) * 1000, 5)
    return arr, metrics


def insertion_sort(records, key="priority", descending=False):
    arr = [dict(r) for r in records]
    metrics = {"comparisons": 0, "swaps": 0}
    start = time.perf_counter()
    for i in range(1, len(arr)):
        current = arr[i]
        j = i - 1
        while j >= 0:
            metrics["comparisons"] += 1
            if compare(arr[j], current, key, descending, None) <= 0:
                break
            arr[j + 1] = arr[j]
            metrics["swaps"] += 1
            j -= 1
        arr[j + 1] = current
    metrics["time_ms"] = round((time.perf_counter() - start) * 1000, 5)
    return arr, metrics


def selection_sort(records, key="priority", descending=False):
    arr = [dict(r) for r in records]
    metrics = {"comparisons": 0, "swaps": 0}
    start = time.perf_counter()
    n = len(arr)
    for i in range(n - 1):
        best = i
        for j in range(i + 1, n):
            metrics["comparisons"] += 1
            if compare(arr[j], arr[best], key, descending, None) < 0:
                best = j
        swap(arr, i, best, metrics)
    metrics["time_ms"] = round((time.perf_counter() - start) * 1000, 5)
    return arr, metrics


def bubble_sort(records, key="priority", descending=False):
    arr = [dict(r) for r in records]
    metrics = {"comparisons": 0, "swaps": 0}
    start = time.perf_counter()
    n = len(arr)
    for i in range(n):
        changed = False
        for j in range(0, n - i - 1):
            metrics["comparisons"] += 1
            if compare(arr[j], arr[j + 1], key, descending, None) > 0:
                swap(arr, j, j + 1, metrics)
                changed = True
        if not changed:
            break
    metrics["time_ms"] = round((time.perf_counter() - start) * 1000, 5)
    return arr, metrics


SORTERS = {
    "Quick Sort": quick_sort,
    "Merge Sort": merge_sort,
    "Insertion Sort": insertion_sort,
    "Selection Sort": selection_sort,
    "Bubble Sort": bubble_sort,
}
