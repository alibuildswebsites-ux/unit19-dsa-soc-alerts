"""Repeatable benchmark and memory profile for the Unit 19 report.

All numbers are collected at runtime; no sample measurements are hard-coded.
"""

from __future__ import annotations

import csv
import bisect
import gc
import json
import os
import platform
import random
import statistics
import sys
import time
import tracemalloc
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from soc_alerts.models import Alert, Severity
from soc_alerts.structures import LinkedQueue, PriorityAlertQueue
from soc_alerts.sorting import insertion_sort, merge_sort

RESULTS = ROOT / "results"
BASE_TIME = datetime(2026, 5, 1, tzinfo=timezone.utc)


def median_ms(operation, repeats: int = 5) -> float:
    samples = []
    for _ in range(repeats):
        gc.collect()
        start = time.perf_counter_ns()
        operation()
        samples.append((time.perf_counter_ns() - start) / 1_000_000)
    return round(statistics.median(samples), 4)


def make_alerts(size: int, seed: int = 1904) -> list[Alert]:
    generator = random.Random(seed)
    severities = list(Severity)
    return [
        Alert(
            identifier=f"BENCH-{index:06d}",
            severity=generator.choice(severities),
            received_at=BASE_TIME + timedelta(microseconds=index),
        )
        for index in range(size)
    ]


def linked_queue_cycle(values: list[int]) -> None:
    queue: LinkedQueue[int] = LinkedQueue()
    for value in values:
        queue.enqueue(value)
    while not queue.is_empty():
        queue.dequeue()


def list_queue_cycle(values: list[int]) -> None:
    queue = []
    for value in values:
        queue.append(value)
    while queue:
        queue.pop(0)


def heap_priority_cycle(alerts: list[Alert]) -> None:
    queue = PriorityAlertQueue()
    for alert in alerts:
        queue.add(alert)
    while not queue.is_empty():
        queue.pop()


def sorted_list_priority_cycle(alerts: list[Alert]) -> None:
    """Maintain the same priority ordering by binary insertion into a Python list."""
    entries = []
    for index, alert in enumerate(alerts):
        key = (int(alert.severity), -alert.received_at.timestamp(), -index)
        bisect.insort(entries, (key, alert))
    while entries:
        entries.pop()


def insertion_cycle(values: list[int]) -> None:
    work = values.copy()
    insertion_sort(work)


def merge_cycle(values: list[int]) -> None:
    merge_sort(values)


def peak_bytes(factory, size: int) -> int:
    gc.collect()
    tracemalloc.start()
    try:
        _object = factory(size)
        _, peak = tracemalloc.get_traced_memory()
        return int(peak)
    finally:
        tracemalloc.stop()


def linked_factory(size: int):
    queue: LinkedQueue[int] = LinkedQueue()
    for number in range(size):
        queue.enqueue(number)
    return queue


def list_factory(size: int):
    return list(range(size))


def main() -> None:
    RESULTS.mkdir(exist_ok=True)
    dataset_sizes = [250, 1_000, 4_000, 16_000]
    queue_rows = []
    priority_rows = []
    sort_rows = []

    for size in dataset_sizes:
        values = list(range(size))
        queue_rows.append({
            "n": size,
            "linked_queue_ms": median_ms(lambda: linked_queue_cycle(values)),
            "python_list_fifo_ms": median_ms(lambda: list_queue_cycle(values)),
        })
        alerts = make_alerts(size)
        priority_rows.append({
            "n": size,
            "binary_heap_ms": median_ms(lambda: heap_priority_cycle(alerts)),
            "sorted_list_ms": median_ms(lambda: sorted_list_priority_cycle(alerts)),
        })

    sort_sizes = [100, 500, 1_500]
    for size in sort_sizes:
        generator = random.Random(1904 + size)
        values = [generator.randrange(0, size * 4) for _ in range(size)]
        sort_rows.append({
            "n": size,
            "insertion_sort_ms": median_ms(lambda: insertion_cycle(values)),
            "merge_sort_ms": median_ms(lambda: merge_cycle(values)),
        })

    memory_size = 5_000
    memory = {
        "n": memory_size,
        "python_list_peak_bytes": peak_bytes(list_factory, memory_size),
        "linked_queue_peak_bytes": peak_bytes(linked_factory, memory_size),
        "measurement": "tracemalloc peak traced Python allocations; one build per structure",
    }

    output = {
        "metadata": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "processor": platform.processor() or "not reported by platform",
            "cpu_count": os.cpu_count(),
            "timer": "time.perf_counter_ns",
            "repeats": 5,
            "summary": "median of five independent runs after garbage collection",
            "seed": 1904,
        },
        "fifo_scaling": queue_rows,
        "priority_scaling": priority_rows,
        "sorting_scaling": sort_rows,
        "memory_profile": memory,
    }
    json_path = RESULTS / "benchmark-results.json"
    json_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    for name, rows in [
        ("fifo_scaling.csv", queue_rows),
        ("priority_scaling.csv", priority_rows),
        ("sorting_scaling.csv", sort_rows),
    ]:
        with (RESULTS / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
