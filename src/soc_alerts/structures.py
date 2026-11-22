"""Custom queue, stack and binary max-heap implementations.

These educational implementations deliberately avoid wrapping collections.deque
or heapq so the core operations and invariants remain visible to the learner.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Generic, Iterator, TypeVar, cast

from .models import Alert

T = TypeVar("T")


class QueueEmptyError(IndexError):
    """Raised when removing or inspecting an empty queue/heap."""


class QueueFullError(OverflowError):
    """Raised when an optional queue/heap capacity has been reached."""


class StackEmptyError(IndexError):
    """Raised when popping or peeking an empty stack."""


class StackOverflowError(OverflowError):
    """Raised when a fixed-capacity stack is full."""


@dataclass(slots=True)
class _Node(Generic[T]):
    value: T
    next: "_Node[T] | None" = None


class LinkedQueue(Generic[T]):
    """Singly linked FIFO queue with O(1) enqueue and dequeue."""

    __slots__ = ("_head", "_tail", "_size", "_capacity")

    def __init__(self, capacity: int | None = None) -> None:
        if capacity is not None and capacity < 1:
            raise ValueError("capacity must be positive or None")
        self._head: _Node[T] | None = None
        self._tail: _Node[T] | None = None
        self._size = 0
        self._capacity = capacity

    def enqueue(self, value: T) -> None:
        # Reject overload before allocating a node, preserving the size invariant.
        if self._capacity is not None and self._size >= self._capacity:
            raise QueueFullError("queue capacity reached")
        node = _Node(value)
        if self._tail is None:
            self._head = self._tail = node
        else:
            self._tail.next = node
            self._tail = node
        self._size += 1

    def dequeue(self) -> T:
        # Advance the head once; clear the tail when the final node is removed.
        if self._head is None:
            raise QueueEmptyError("cannot dequeue from an empty queue")
        node = self._head
        self._head = node.next
        self._size -= 1
        if self._head is None:
            self._tail = None
        return node.value

    def peek(self) -> T:
        if self._head is None:
            raise QueueEmptyError("cannot peek at an empty queue")
        return self._head.value

    def is_empty(self) -> bool:
        return self._size == 0

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[T]:
        current = self._head
        while current is not None:
            yield current.value
            current = current.next


class ArrayStack(Generic[T]):
    """Fixed-capacity array stack with O(1) push, pop and peek."""

    __slots__ = ("_items", "_top", "_capacity")

    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("stack capacity must be positive")
        self._capacity = capacity
        self._items: list[T | None] = [None] * capacity
        self._top = -1

    def push(self, value: T) -> None:
        # The next free slot is one position above the current top index.
        if self._top + 1 >= self._capacity:
            raise StackOverflowError("stack capacity reached")
        self._top += 1
        self._items[self._top] = value

    def pop(self) -> T:
        # Clear the released slot so removed objects are not retained by the array.
        if self._top < 0:
            raise StackEmptyError("cannot pop from an empty stack")
        value = cast(T, self._items[self._top])
        self._items[self._top] = None
        self._top -= 1
        return value

    def peek(self) -> T:
        if self._top < 0:
            raise StackEmptyError("cannot peek at an empty stack")
        return cast(T, self._items[self._top])

    def is_empty(self) -> bool:
        return self._top == -1

    def is_full(self) -> bool:
        return self._top + 1 == self._capacity

    def __len__(self) -> int:
        return self._top + 1


@dataclass(frozen=True, slots=True)
class _HeapEntry:
    key: tuple[int, float, int]
    alert: Alert


class PriorityAlertQueue:
    """Binary max-heap: severity desc, receive time asc, then stable FIFO."""

    __slots__ = ("_heap", "_sequence", "_capacity")

    def __init__(self, capacity: int | None = None) -> None:
        if capacity is not None and capacity < 1:
            raise ValueError("capacity must be positive or None")
        self._heap: list[_HeapEntry] = []
        self._sequence = 0
        self._capacity = capacity

    @staticmethod
    def _priority_key(alert: Alert, sequence: int) -> tuple[int, float, int]:
        # Negating the timestamp and sequence makes earlier values larger in a max-heap.
        return (int(alert.severity), -alert.received_at.timestamp(), -sequence)

    def add(self, alert: Alert) -> None:
        if self._capacity is not None and len(self._heap) >= self._capacity:
            raise QueueFullError("priority queue capacity reached")
        entry = _HeapEntry(self._priority_key(alert, self._sequence), alert)
        self._sequence += 1
        self._heap.append(entry)
        self._sift_up(len(self._heap) - 1)

    def pop(self) -> Alert:
        if not self._heap:
            raise QueueEmptyError("cannot pop from an empty priority queue")
        root = self._heap[0].alert
        last = self._heap.pop()
        if self._heap:
            self._heap[0] = last
            self._sift_down(0)
        return root

    def peek(self) -> Alert:
        if not self._heap:
            raise QueueEmptyError("cannot peek at an empty priority queue")
        return self._heap[0].alert

    def is_empty(self) -> bool:
        return not self._heap

    def __len__(self) -> int:
        return len(self._heap)

    def _sift_up(self, index: int) -> None:
        # Restore parent >= child ordering along the inserted node's path.
        while index > 0:
            parent = (index - 1) // 2
            if self._heap[parent].key >= self._heap[index].key:
                break
            self._heap[parent], self._heap[index] = self._heap[index], self._heap[parent]
            index = parent

    def _sift_down(self, index: int) -> None:
        # Move the larger child upward until the max-heap invariant holds.
        size = len(self._heap)
        while True:
            left = 2 * index + 1
            right = left + 1
            largest = index
            if left < size and self._heap[left].key > self._heap[largest].key:
                largest = left
            if right < size and self._heap[right].key > self._heap[largest].key:
                largest = right
            if largest == index:
                return
            self._heap[index], self._heap[largest] = self._heap[largest], self._heap[index]
            index = largest
