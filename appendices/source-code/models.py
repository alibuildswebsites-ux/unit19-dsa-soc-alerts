"""Immutable domain objects for the SOC alert-management example."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import IntEnum, StrEnum


class Severity(IntEnum):
    """Numeric severity; larger values represent greater urgency.

    IntEnum makes the order explicit so the priority key can compare severity
    without relying on arbitrary input strings.
    """

    INFO = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5

    @classmethod
    def parse(cls, value: "Severity | str") -> "Severity":
        """Parse a severity name without accepting unknown or ambiguous values."""
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            raise ValueError("severity must be a Severity or string name")
        try:
            return cls[value.strip().upper()]
        except KeyError as exc:
            raise ValueError(f"unknown severity: {value!r}") from exc


class AlertStatus(StrEnum):
    """Explicit lifecycle states for an alert record."""

    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


@dataclass(frozen=True, slots=True)
class Alert:
    """Immutable alert snapshot; managers replace snapshots on state changes.

    Keeping timestamps timezone-aware makes arrival ordering comparable across
    event sources and avoids mixing local naive times with UTC-aware values.
    """

    identifier: str
    severity: Severity
    received_at: datetime
    status: AlertStatus = AlertStatus.QUEUED
    updated_at: datetime | None = None
    source: str = "unspecified"

    def __post_init__(self) -> None:
        normalized = self.identifier.strip() if isinstance(self.identifier, str) else ""
        if not normalized:
            raise ValueError("alert identifier must be a non-empty string")
        if not isinstance(self.severity, Severity):
            raise TypeError("severity must be a Severity value")
        self._check_aware(self.received_at, "received_at")
        if self.updated_at is None:
            object.__setattr__(self, "updated_at", self.received_at)
        else:
            self._check_aware(self.updated_at, "updated_at")
        object.__setattr__(self, "identifier", normalized)
        if not isinstance(self.status, AlertStatus):
            raise TypeError("status must be an AlertStatus value")

    @staticmethod
    def _check_aware(value: datetime, field_name: str) -> None:
        if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{field_name} must be a timezone-aware datetime")


@dataclass(frozen=True, slots=True)
class AlertEvent:
    """Immutable notification sent to subscribed analyst clients."""

    event_type: str
    alert: Alert
    emitted_at: datetime

    def __post_init__(self) -> None:
        Alert._check_aware(self.emitted_at, "emitted_at")
