"""Domain models and value objects for the triage queue."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import IntEnum
from typing import Any, Optional
import uuid

from triage_queue.exceptions import EmptyNameError, InvalidTriageLevelError


class TriageLevel(IntEnum):
    """Clinical severity levels for emergency triage."""

    CRITICAL = 1
    URGENT = 2
    STANDARD = 3

    @classmethod
    def from_value(cls, val: Any) -> "TriageLevel":
        """Parse an integer or string into a valid TriageLevel enum member."""
        if isinstance(val, cls):
            return val
        if isinstance(val, bool):
            raise InvalidTriageLevelError("Boolean cannot be converted to TriageLevel")
        if isinstance(val, (int, str)):
            try:
                int_val = int(val)
                return cls(int_val)
            except (ValueError, TypeError) as err:
                raise InvalidTriageLevelError(
                    f"Invalid triage level {val!r}. Must be 1 (Critical), 2 (Urgent), or 3 (Standard)."
                ) from err
        raise InvalidTriageLevelError(
            f"Invalid triage level type {type(val).__name__}. Expected integer or string."
        )

    @property
    def label(self) -> str:
        """Return human-readable severity label."""
        labels = {
            TriageLevel.CRITICAL: "Critical",
            TriageLevel.URGENT: "Urgent",
            TriageLevel.STANDARD: "Standard",
        }
        return labels[self]


@dataclass(frozen=True)
class PatientRecord:
    """Immutable record of an admitted patient."""

    id: str
    name: str
    triage_level: TriageLevel
    arrived_at: datetime

    @classmethod
    def create(
        cls,
        name: str,
        triage_level: TriageLevel | int | str,
        arrived_at: Optional[datetime] = None,
        patient_id: Optional[str] = None,
    ) -> "PatientRecord":
        """Factory method to validate parameters and construct an immutable PatientRecord."""
        if not isinstance(name, str):
            raise EmptyNameError("Patient name must be a string.")
        cleaned_name = name.strip()
        if not cleaned_name:
            raise EmptyNameError("Patient name cannot be blank.")

        level = TriageLevel.from_value(triage_level)

        if arrived_at is None:
            arrival_dt = datetime.now(timezone.utc)
        elif not isinstance(arrived_at, datetime):
            raise TypeError("arrived_at must be an instance of datetime")
        elif arrived_at.tzinfo is None:
            arrival_dt = arrived_at.replace(tzinfo=timezone.utc)
        else:
            arrival_dt = arrived_at

        pid = patient_id.strip() if (patient_id and isinstance(patient_id, str)) else f"PT-{uuid.uuid4().hex[:8].upper()}"

        return cls(
            id=pid,
            name=cleaned_name,
            triage_level=level,
            arrived_at=arrival_dt,
        )


@dataclass(frozen=True)
class QueueStatistics:
    """Summary workload statistics for emergency triage queue."""

    critical_count: int
    urgent_count: int
    standard_count: int
    total_count: int

    def __post_init__(self) -> None:
        """Validate invariant constraints."""
        if self.critical_count < 0:
            raise ValueError("critical_count must be non-negative")
        if self.urgent_count < 0:
            raise ValueError("urgent_count must be non-negative")
        if self.standard_count < 0:
            raise ValueError("standard_count must be non-negative")
        expected_total = self.critical_count + self.urgent_count + self.standard_count
        if self.total_count != expected_total:
            raise ValueError(f"total_count ({self.total_count}) must equal sum of tier counts ({expected_total})")

