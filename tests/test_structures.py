from datetime import datetime, timezone, timedelta

import pytest

from soc_alerts.models import Alert, Severity
from soc_alerts.structures import (
    ArrayStack,
    LinkedQueue,
    PriorityAlertQueue,
    QueueEmptyError,
    QueueFullError,
    StackEmptyError,
    StackOverflowError,
)


def make_alert(identifier: str, severity: Severity, seconds: int) -> Alert:
    moment = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=seconds)
    return Alert(identifier, severity, moment, updated_at=moment)


def test_linked_queue_is_fifo_and_clears_tail_after_last_dequeue():
    queue: LinkedQueue[int] = LinkedQueue()
    queue.enqueue(10)
    queue.enqueue(20)
    assert queue.peek() == 10
    assert queue.dequeue() == 10
    assert queue.dequeue() == 20
    assert queue.is_empty()
    queue.enqueue(30)
    assert queue.dequeue() == 30


def test_linked_queue_rejects_empty_operations_and_capacity_overflow():
    queue: LinkedQueue[int] = LinkedQueue(capacity=1)
    with pytest.raises(QueueEmptyError):
        queue.dequeue()
    with pytest.raises(QueueEmptyError):
        queue.peek()
    queue.enqueue(1)
    with pytest.raises(QueueFullError):
        queue.enqueue(2)


def test_array_stack_is_lifo_and_reports_empty_and_overflow():
    stack: ArrayStack[str] = ArrayStack(capacity=2)
    stack.push("first")
    stack.push("second")
    assert stack.peek() == "second"
    assert stack.pop() == "second"
    assert stack.pop() == "first"
    with pytest.raises(StackEmptyError):
        stack.pop()
    with pytest.raises(StackEmptyError):
        stack.peek()
    stack.push("a")
    stack.push("b")
    with pytest.raises(StackOverflowError):
        stack.push("c")


def test_priority_queue_orders_severity_then_timestamp_then_insertion_stability():
    queue = PriorityAlertQueue()
    queue.add(make_alert("routine", Severity.LOW, 0))
    queue.add(make_alert("later-critical", Severity.CRITICAL, 20))
    queue.add(make_alert("earlier-critical", Severity.CRITICAL, 10))
    queue.add(make_alert("same-time-first", Severity.HIGH, 30))
    queue.add(make_alert("same-time-second", Severity.HIGH, 30))
    assert [queue.pop().identifier for _ in range(5)] == [
        "earlier-critical",
        "later-critical",
        "same-time-first",
        "same-time-second",
        "routine",
    ]


def test_priority_queue_empty_and_capacity_errors():
    queue = PriorityAlertQueue(capacity=1)
    with pytest.raises(QueueEmptyError):
        queue.pop()
    queue.add(make_alert("one", Severity.HIGH, 1))
    with pytest.raises(QueueFullError):
        queue.add(make_alert("two", Severity.LOW, 2))


def test_priority_queue_peek_does_not_remove_item():
    queue = PriorityAlertQueue()
    alert = make_alert("peek-me", Severity.CRITICAL, 0)
    queue.add(alert)
    assert queue.peek() == alert
    assert len(queue) == 1
    assert queue.pop() == alert
