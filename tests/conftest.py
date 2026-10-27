"""Shared pytest fixtures and test data generators for triage_queue tests."""

from datetime import datetime, timezone, timedelta
from typing import Callable
import pytest

from triage_queue.models import PatientRecord, TriageLevel
from triage_queue.queue import TriageQueue


@pytest.fixture
def base_time() -> datetime:
    """Provide a fixed timezone-aware base timestamp for deterministic tests."""
    return datetime(2026, 10, 27, 10, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def patient_factory(base_time: datetime) -> Callable[..., PatientRecord]:
    """Factory fixture for creating PatientRecord instances with default values."""
    counter = 0

    def _create(
        name: str = "Test Patient",
        triage_level: TriageLevel | int = TriageLevel.STANDARD,
        offset_seconds: int = 0,
        patient_id: str | None = None,
    ) -> PatientRecord:
        nonlocal counter
        counter += 1
        arrived_at = base_time + timedelta(seconds=offset_seconds)
        pid = patient_id or f"PT-{1000 + counter}"
        return PatientRecord.create(
            name=name,
            triage_level=triage_level,
            arrived_at=arrived_at,
            patient_id=pid,
        )

    return _create


@pytest.fixture
def empty_queue() -> TriageQueue:
    """Fixture providing a fresh, empty TriageQueue instance."""
    return TriageQueue()


@pytest.fixture
def populated_queue(patient_factory: Callable[..., PatientRecord]) -> TriageQueue:
    """Fixture providing a queue pre-populated with diverse patients across tiers."""
    queue = TriageQueue()
    # Admitted in non-priority order to test queue sorting
    p_std = patient_factory(name="Standard Bob", triage_level=TriageLevel.STANDARD, offset_seconds=0)
    p_urg = patient_factory(name="Urgent Jane", triage_level=TriageLevel.URGENT, offset_seconds=10)
    p_crit = patient_factory(name="Critical Alice", triage_level=TriageLevel.CRITICAL, offset_seconds=20)
    queue.enqueue(p_std)
    queue.enqueue(p_urg)
    queue.enqueue(p_crit)
    return queue
