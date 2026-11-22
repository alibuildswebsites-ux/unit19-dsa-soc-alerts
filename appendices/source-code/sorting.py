"""Two stable sorting algorithms for the Pearson M2 comparison."""

from __future__ import annotations

from collections.abc import Callable, MutableSequence, Sequence
from typing import TypeVar

T = TypeVar("T")
K = TypeVar("K")


def insertion_sort(values: MutableSequence[T], key: Callable[[T], K] | None = None) -> None:
    """Stable in-place insertion sort; O(n^2) worst-case time, O(1) auxiliary space."""
    key_fn: Callable[[T], object] = key or (lambda item: item)
    # Each pass inserts one value into the already sorted prefix.
    for index in range(1, len(values)):
        current = values[index]
        current_key = key_fn(current)
        cursor = index - 1
        # Strict comparison keeps equal-key items in their original order.
        while cursor >= 0 and key_fn(values[cursor]) > current_key:
            values[cursor + 1] = values[cursor]
            cursor -= 1
        values[cursor + 1] = current


def merge_sort(values: Sequence[T], key: Callable[[T], K] | None = None) -> list[T]:
    """Stable iterative merge sort; O(n log n) time and O(n) auxiliary space."""
    key_fn: Callable[[T], object] = key or (lambda item: item)
    result = list(values)
    size = len(result)
    if size < 2:
        return result
    scratch = result.copy()
    width = 1
    # Merge adjacent runs of width 1, 2, 4... until the full list is sorted.
    while width < size:
        for start in range(0, size, 2 * width):
            middle = min(start + width, size)
            end = min(start + 2 * width, size)
            left, right, output = start, middle, start
            while left < middle and right < end:
                # Taking left on equality is the stability condition.
                if key_fn(result[left]) <= key_fn(result[right]):
                    scratch[output] = result[left]
                    left += 1
                else:
                    scratch[output] = result[right]
                    right += 1
                output += 1
            while left < middle:
                scratch[output] = result[left]
                left += 1
                output += 1
            while right < end:
                scratch[output] = result[right]
                right += 1
                output += 1
        result, scratch = scratch, result
        width *= 2
    return result
