"""Thread-safe coordinator for alert storage, scheduling and analyst updates."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from threading import RLock
from typing import Callable

from .models import Alert, AlertEvent, AlertStatus, Severity
from .structures import ArrayStack, LinkedQueue, PriorityAlertQueue, QueueEmptyError


class DuplicateAlertError(ValueError):
    """An alert identifier is already present in the in-memory store."""


class InvalidSeverityError(ValueError):
    """A severity value is not one of the supported levels."""


class AlertCapacityError(OverflowError):
    """The manager's configured record capacity has been reached."""


class AlertNotFoundError(KeyError):
    """The requested alert identifier is not present."""


class InvalidStatusTransitionError(ValueError):
    """An alert lifecycle transition is not permitted."""


AlertListener = Callable[[AlertEvent], None]


class AlertManager:
    """Encapsulate alert records and their routine/priority processing paths."""

    _ALLOWED_TRANSITIONS = {
        AlertStatus.QUEUED: {AlertStatus.IN_PROGRESS, AlertStatus.DISMISSED},
        AlertStatus.IN_PROGRESS: {AlertStatus.RESOLVED, AlertStatus.DISMISSED},
        AlertStatus.RESOLVED: set(),
        AlertStatus.DISMISSED: set(),
    }

    def __init__(
        self,
        capacity: int = 10_000,
        history_capacity: int = 256,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if capacity < 1:
            raise ValueError("capacity must be positive")
        if history_capacity < 1:
            raise ValueError("history capacity must be positive")
        self._capacity = capacity
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._routine: LinkedQueue[Alert] = LinkedQueue(capacity)
        self._priority = PriorityAlertQueue(capacity)
        self._by_id: dict[str, Alert] = {}
        self._analyst_actions: ArrayStack[str] = ArrayStack(history_capacity)
        self._listeners: list[AlertListener] = []
        self._listener_errors: list[str] = []
        self._lock = RLock()

    def add_alert(
        self,
        identifier: str,
        severity: Severity | str,
        *,
        received_at: datetime | None = None,
        source: str = "unspecified",
    ) -> Alert:
        """Validate, store and schedule an alert; then notify observers."""
        try:
            parsed_severity = Severity.parse(severity)
        except ValueError as exc:
            raise InvalidSeverityError(str(exc)) from exc
        moment = received_at or self._clock()
        try:
            alert = Alert(identifier, parsed_severity, moment, AlertStatus.QUEUED, moment, source)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid alert: {exc}") from exc

        with self._lock:
            if alert.identifier in self._by_id:
                raise DuplicateAlertError(f"alert {alert.identifier!r} already exists")
            if len(self._by_id) >= self._capacity:
                raise AlertCapacityError("alert store capacity reached")
            if parsed_severity >= Severity.HIGH:
                self._priority.add(alert)
            else:
                self._routine.enqueue(alert)
            self._by_id[alert.identifier] = alert
            event, listeners = self._make_event("alert_added", alert)
        self._dispatch(event, listeners)
        return alert

    def process_next(self) -> Alert:
        """Select the most urgent alert, set it in progress and publish an event."""
        with self._lock:
            while not self._priority.is_empty() or not self._routine.is_empty():
                candidate = self._priority.pop() if not self._priority.is_empty() else self._routine.dequeue()
                current = self._by_id[candidate.identifier]
                # A queued alert may have been dismissed while waiting in the structure.
                if current.status is not AlertStatus.QUEUED:
                    continue
                updated = replace(current, status=AlertStatus.IN_PROGRESS, updated_at=self._clock())
                self._by_id[updated.identifier] = updated
                event, listeners = self._make_event("alert_processing", updated)
                break
            else:
                raise QueueEmptyError("no queued alerts are available")
        self._dispatch(event, listeners)
        return updated

    def update_status(self, identifier: str, new_status: AlertStatus) -> Alert:
        """Apply an allowed state transition and publish the immutable new snapshot."""
        if not isinstance(new_status, AlertStatus):
            raise TypeError("new_status must be an AlertStatus value")
        with self._lock:
            current = self._by_id.get(identifier)
            if current is None:
                raise AlertNotFoundError(identifier)
            if new_status not in self._ALLOWED_TRANSITIONS[current.status]:
                raise InvalidStatusTransitionError(
                    f"cannot change {current.status.value} to {new_status.value}"
                )
            updated = replace(current, status=new_status, updated_at=self._clock())
            self._by_id[identifier] = updated
            event, listeners = self._make_event("alert_status_changed", updated)
        self._dispatch(event, listeners)
        return updated

    def get_alert(self, identifier: str) -> Alert:
        """Return an immutable snapshot, preventing callers bypassing validation."""
        with self._lock:
            try:
                return self._by_id[identifier]
            except KeyError as exc:
                raise AlertNotFoundError(identifier) from exc

    def subscribe(self, listener: AlertListener) -> None:
        """Register a callback for alert lifecycle updates."""
        if not callable(listener):
            raise TypeError("listener must be callable")
        with self._lock:
            if listener not in self._listeners:
                self._listeners.append(listener)

    def unsubscribe(self, listener: AlertListener) -> None:
        """Remove a previously registered callback; unknown listeners are ignored."""
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)

    @property
    def listener_errors(self) -> tuple[str, ...]:
        """Expose a read-only copy of observer failures for operational diagnostics."""
        with self._lock:
            return tuple(self._listener_errors)

    @property
    def queued_counts(self) -> tuple[int, int]:
        """Return (priority_count, routine_count) without exposing the structures."""
        with self._lock:
            return (len(self._priority), len(self._routine))

    def record_analyst_action(self, action: str) -> None:
        """Push the latest analyst action onto a bounded LIFO undo stack."""
        if not isinstance(action, str) or not action.strip():
            raise ValueError("analyst action must be a non-empty string")
        with self._lock:
            self._analyst_actions.push(action.strip())

    def undo_last_action(self) -> str:
        """Pop the newest analyst action; raises StackEmptyError when none exist."""
        with self._lock:
            return self._analyst_actions.pop()

    def __len__(self) -> int:
        with self._lock:
            return len(self._by_id)

    def _make_event(self, event_type: str, alert: Alert) -> tuple[AlertEvent, tuple[AlertListener, ...]]:
        return AlertEvent(event_type, alert, self._clock()), tuple(self._listeners)

    def _dispatch(self, event: AlertEvent, listeners: tuple[AlertListener, ...]) -> None:
        # Never run user-supplied callbacks while holding the manager lock.
        for listener in listeners:
            try:
                listener(event)
            except Exception as exc:  # Observer failure must not roll back core alert state.
                with self._lock:
                    self._listener_errors.append(f"{type(exc).__name__}: {exc}")
