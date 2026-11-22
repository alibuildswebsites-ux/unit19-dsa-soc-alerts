from datetime import datetime, timezone, timedelta

import pytest

from soc_alerts.manager import (
    AlertCapacityError,
    AlertManager,
    AlertNotFoundError,
    DuplicateAlertError,
    InvalidSeverityError,
    InvalidStatusTransitionError,
)
from soc_alerts.models import AlertStatus
from soc_alerts.structures import QueueEmptyError


BASE = datetime(2026, 5, 1, 9, 0, tzinfo=timezone.utc)


def test_manager_prioritises_critical_incidents_and_keeps_routine_fifo():
    manager = AlertManager(capacity=10)
    manager.add_alert("r1", "low", received_at=BASE)
    manager.add_alert("r2", "medium", received_at=BASE + timedelta(seconds=1))
    manager.add_alert("c1", "critical", received_at=BASE + timedelta(seconds=2))
    manager.add_alert("h1", "high", received_at=BASE + timedelta(seconds=3))
    assert [manager.process_next().identifier for _ in range(4)] == ["c1", "h1", "r1", "r2"]


def test_manager_stores_immutable_snapshots_and_updates_status_timestamps():
    manager = AlertManager(capacity=3, clock=lambda: BASE + timedelta(minutes=1))
    alert = manager.add_alert("auth-17", "high", received_at=BASE)
    assert alert.status is AlertStatus.QUEUED
    assert manager.get_alert("auth-17").received_at == BASE
    processed = manager.process_next()
    assert processed.status is AlertStatus.IN_PROGRESS
    assert processed.updated_at == BASE + timedelta(minutes=1)
    resolved = manager.update_status("auth-17", AlertStatus.RESOLVED)
    assert resolved.status is AlertStatus.RESOLVED
    assert manager.get_alert("auth-17").status is AlertStatus.RESOLVED


def test_manager_rejects_duplicate_identifiers_invalid_severity_and_capacity():
    manager = AlertManager(capacity=1)
    manager.add_alert("same", "low", received_at=BASE)
    with pytest.raises(DuplicateAlertError):
        manager.add_alert("same", "high", received_at=BASE)
    with pytest.raises(InvalidSeverityError):
        manager.add_alert("bad-severity", "urgent-ish", received_at=BASE)
    with pytest.raises(AlertCapacityError):
        manager.add_alert("overflow", "low", received_at=BASE)


def test_manager_handles_empty_queue_missing_ids_and_invalid_transitions():
    manager = AlertManager(capacity=5)
    with pytest.raises(QueueEmptyError):
        manager.process_next()
    with pytest.raises(AlertNotFoundError):
        manager.get_alert("missing")
    manager.add_alert("x", "low", received_at=BASE)
    with pytest.raises(InvalidStatusTransitionError):
        manager.update_status("x", AlertStatus.RESOLVED)


def test_manager_publishes_real_time_events_and_isolates_listener_failures():
    manager = AlertManager(capacity=5)
    observed = []

    def good_listener(event):
        observed.append((event.event_type, event.alert.identifier, event.alert.status))

    def broken_listener(event):
        raise RuntimeError("observer unavailable")

    manager.subscribe(good_listener)
    manager.subscribe(broken_listener)
    manager.add_alert("evt-1", "critical", received_at=BASE)
    manager.process_next()
    manager.update_status("evt-1", AlertStatus.RESOLVED)
    assert [item[0] for item in observed] == ["alert_added", "alert_processing", "alert_status_changed"]
    assert len(manager.listener_errors) == 3
    manager.unsubscribe(broken_listener)
    manager.add_alert("evt-2", "low", received_at=BASE)
    assert len(manager.listener_errors) == 3


def test_manager_stack_tracks_analyst_actions_in_lifo_order():
    manager = AlertManager(capacity=5, history_capacity=2)
    manager.record_analyst_action("acknowledged A")
    manager.record_analyst_action("assigned B")
    assert manager.undo_last_action() == "assigned B"
    assert manager.undo_last_action() == "acknowledged A"


def test_manager_skips_alerts_dismissed_while_waiting_in_fifo():
    manager = AlertManager(capacity=5)
    manager.add_alert("dismiss", "low", received_at=BASE)
    manager.add_alert("keep", "low", received_at=BASE + timedelta(seconds=1))
    manager.update_status("dismiss", AlertStatus.DISMISSED)
    assert manager.process_next().identifier == "keep"
    with pytest.raises(QueueEmptyError):
        manager.process_next()


def test_manager_rejects_invalid_action_and_action_stack_overflow():
    manager = AlertManager(capacity=5, history_capacity=1)
    with pytest.raises(ValueError):
        manager.record_analyst_action("  ")
    manager.record_analyst_action("acknowledge")
    from soc_alerts.structures import StackOverflowError
    with pytest.raises(StackOverflowError):
        manager.record_analyst_action("assign")


def test_manager_is_safe_for_concurrent_unique_alert_ingestion():
    from concurrent.futures import ThreadPoolExecutor

    manager = AlertManager(capacity=100)
    with ThreadPoolExecutor(max_workers=8) as executor:
        alerts = list(executor.map(lambda i: manager.add_alert(f"parallel-{i}", "low", received_at=BASE), range(50)))
    assert len(alerts) == 50
    assert len(manager) == 50
    assert manager.queued_counts == (0, 50)
