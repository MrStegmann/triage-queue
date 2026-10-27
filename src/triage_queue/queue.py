"""TriageQueue aggregate managing multi-bucket priority queue."""

from collections import deque
from typing import Deque, Dict, Optional

from triage_queue.models import PatientRecord, QueueStatistics, TriageLevel


class TriageQueue:
    """Multi-bucket priority queue for emergency department patient triage."""

    def __init__(self) -> None:
        """Initialize an empty triage queue with discrete priority buckets."""
        self._buckets: Dict[TriageLevel, Deque[PatientRecord]] = {
            TriageLevel.CRITICAL: deque(),
            TriageLevel.URGENT: deque(),
            TriageLevel.STANDARD: deque(),
        }
        self._total_admitted: int = 0

    def enqueue(self, patient: PatientRecord) -> None:
        """Add a patient to the queue at the end of their respective triage tier."""
        if not isinstance(patient, PatientRecord):
            raise TypeError(f"Expected PatientRecord instance, got {type(patient).__name__}")
        self._buckets[patient.triage_level].append(patient)
        self._total_admitted += 1

    def dequeue(self) -> Optional[PatientRecord]:
        """Remove and return the highest-priority patient waiting the longest."""
        for level in (TriageLevel.CRITICAL, TriageLevel.URGENT, TriageLevel.STANDARD):
            bucket = self._buckets[level]
            if bucket:
                return bucket.popleft()
        return None

    def peek(self) -> Optional[PatientRecord]:
        """Return the next patient due for service without removing them from the queue."""
        for level in (TriageLevel.CRITICAL, TriageLevel.URGENT, TriageLevel.STANDARD):
            bucket = self._buckets[level]
            if bucket:
                return bucket[0]
        return None

    def list_all(self) -> tuple[PatientRecord, ...]:
        """Return an immutable snapshot sequence of all waiting patients in service order."""
        return (
            tuple(self._buckets[TriageLevel.CRITICAL])
            + tuple(self._buckets[TriageLevel.URGENT])
            + tuple(self._buckets[TriageLevel.STANDARD])
        )

    def get_statistics(self) -> QueueStatistics:
        """Return aggregate summary counts by triage tier."""
        crit = len(self._buckets[TriageLevel.CRITICAL])
        urg = len(self._buckets[TriageLevel.URGENT])
        std = len(self._buckets[TriageLevel.STANDARD])
        return QueueStatistics(
            critical_count=crit,
            urgent_count=urg,
            standard_count=std,
            total_count=crit + urg + std,
        )

    def is_empty(self) -> bool:
        """Return True if no patients are currently waiting, False otherwise."""
        return len(self) == 0

    def __len__(self) -> int:
        """Return the total number of waiting patients across all tiers."""
        return sum(len(bucket) for bucket in self._buckets.values())


