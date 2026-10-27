"""Unit tests for TriageQueue priority, FIFO, and empty queue handling."""

from typing import Callable
import pytest

from triage_queue.models import PatientRecord, TriageLevel
from triage_queue.queue import TriageQueue


class TestTriageQueueUS1:
    """Tests for User Story 1 (Intake and Prioritized Service Call)."""

    def test_empty_queue_initial_state(self, empty_queue: TriageQueue) -> None:
        """Verify new queue is empty and dequeue returns None without error."""
        assert empty_queue.is_empty()
        assert len(empty_queue) == 0
        assert empty_queue.dequeue() is None

    def test_enqueue_single_patient(
        self,
        empty_queue: TriageQueue,
        patient_factory: Callable[..., PatientRecord],
    ) -> None:
        """Verify enqueuing a patient updates length and dequeue returns that patient."""
        patient = patient_factory(name="John Doe", triage_level=TriageLevel.URGENT)
        empty_queue.enqueue(patient)

        assert not empty_queue.is_empty()
        assert len(empty_queue) == 1

        dequeued = empty_queue.dequeue()
        assert dequeued == patient
        assert empty_queue.is_empty()
        assert len(empty_queue) == 0

    def test_enqueue_invalid_type_raises_type_error(self, empty_queue: TriageQueue) -> None:
        """Verify enqueue raises TypeError if argument is not a PatientRecord."""
        with pytest.raises(TypeError):
            empty_queue.enqueue("not a patient record")  # type: ignore[arg-type]

    def test_priority_ordering_critical_over_urgent_over_standard(
        self,
        empty_queue: TriageQueue,
        patient_factory: Callable[..., PatientRecord],
    ) -> None:
        """Verify Critical patients are called before Urgent, and Urgent before Standard."""
        p_std = patient_factory(name="Standard Bob", triage_level=TriageLevel.STANDARD)
        p_urg = patient_factory(name="Urgent Jane", triage_level=TriageLevel.URGENT)
        p_crit = patient_factory(name="Critical Alice", triage_level=TriageLevel.CRITICAL)

        # Enqueue in reverse order of clinical priority
        empty_queue.enqueue(p_std)
        empty_queue.enqueue(p_urg)
        empty_queue.enqueue(p_crit)

        assert len(empty_queue) == 3

        # Dequeue must return in priority order regardless of arrival
        assert empty_queue.dequeue() == p_crit
        assert empty_queue.dequeue() == p_urg
        assert empty_queue.dequeue() == p_std
        assert empty_queue.dequeue() is None

    def test_strict_fifo_ordering_within_same_priority_tier(
        self,
        empty_queue: TriageQueue,
        patient_factory: Callable[..., PatientRecord],
    ) -> None:
        """Verify that multiple patients in the same triage tier dequeue in exact FIFO arrival order."""
        p1 = patient_factory(name="Urgent First", triage_level=TriageLevel.URGENT, offset_seconds=0)
        p2 = patient_factory(name="Urgent Second", triage_level=TriageLevel.URGENT, offset_seconds=5)
        p3 = patient_factory(name="Urgent Third", triage_level=TriageLevel.URGENT, offset_seconds=10)

        empty_queue.enqueue(p1)
        empty_queue.enqueue(p2)
        empty_queue.enqueue(p3)

        assert empty_queue.dequeue() == p1
        assert empty_queue.dequeue() == p2
        assert empty_queue.dequeue() == p3
        assert empty_queue.dequeue() is None

    def test_interleaved_priority_and_fifo(
        self,
        empty_queue: TriageQueue,
        patient_factory: Callable[..., PatientRecord],
    ) -> None:
        """Verify complex interleaved arrival preserves tier priorities and inner FIFO order."""
        crit1 = patient_factory(name="Crit 1", triage_level=TriageLevel.CRITICAL)
        crit2 = patient_factory(name="Crit 2", triage_level=TriageLevel.CRITICAL)
        urg1 = patient_factory(name="Urg 1", triage_level=TriageLevel.URGENT)
        std1 = patient_factory(name="Std 1", triage_level=TriageLevel.STANDARD)
        std2 = patient_factory(name="Std 2", triage_level=TriageLevel.STANDARD)

        # Sequence of arrivals: Std1, Urg1, Crit1, Std2, Crit2
        empty_queue.enqueue(std1)
        empty_queue.enqueue(urg1)
        empty_queue.enqueue(crit1)
        empty_queue.enqueue(std2)
        empty_queue.enqueue(crit2)

        # Expected dispatch order: Crit1, Crit2, Urg1, Std1, Std2
        assert empty_queue.dequeue() == crit1
        assert empty_queue.dequeue() == crit2
        assert empty_queue.dequeue() == urg1
        assert empty_queue.dequeue() == std1
        assert empty_queue.dequeue() == std2
        assert empty_queue.dequeue() is None


class TestTriageQueueUS2:
    """Tests for User Story 2 (Queue Inspection and Queue Visibility)."""

    def test_peek_empty_queue(self, empty_queue: TriageQueue) -> None:
        """Verify peek returns None on empty queue and maintains len 0."""
        assert empty_queue.peek() is None
        assert len(empty_queue) == 0

    def test_peek_does_not_mutate_queue(
        self,
        empty_queue: TriageQueue,
        patient_factory: Callable[..., PatientRecord],
    ) -> None:
        """Verify peek returns head patient without dequeuing or altering queue length."""
        p_std = patient_factory(name="Std Bob", triage_level=TriageLevel.STANDARD)
        p_crit = patient_factory(name="Crit Alice", triage_level=TriageLevel.CRITICAL)

        empty_queue.enqueue(p_std)
        empty_queue.enqueue(p_crit)

        assert len(empty_queue) == 2

        # Peek should see Critical patient
        peeked1 = empty_queue.peek()
        assert peeked1 == p_crit
        assert len(empty_queue) == 2

        # Second peek returns same patient
        peeked2 = empty_queue.peek()
        assert peeked2 == p_crit
        assert len(empty_queue) == 2

        # Subsequent dequeue returns the peeked patient
        dequeued = empty_queue.dequeue()
        assert dequeued == p_crit
        assert len(empty_queue) == 1

    def test_list_all_empty_queue(self, empty_queue: TriageQueue) -> None:
        """Verify list_all returns empty sequence on empty queue."""
        result = empty_queue.list_all()
        assert isinstance(result, tuple)
        assert len(result) == 0

    def test_list_all_order_and_non_mutating(
        self,
        empty_queue: TriageQueue,
        patient_factory: Callable[..., PatientRecord],
    ) -> None:
        """Verify list_all returns all patients in exact dispatch sequence and does not mutate queue."""
        p_std = patient_factory(name="Std Bob", triage_level=TriageLevel.STANDARD)
        p_urg = patient_factory(name="Urg Jane", triage_level=TriageLevel.URGENT)
        p_crit = patient_factory(name="Crit Alice", triage_level=TriageLevel.CRITICAL)

        empty_queue.enqueue(p_std)
        empty_queue.enqueue(p_urg)
        empty_queue.enqueue(p_crit)

        snapshot = empty_queue.list_all()
        assert isinstance(snapshot, tuple)
        assert len(snapshot) == 3
        assert snapshot == (p_crit, p_urg, p_std)

        # Ensure queue length and dequeue order are unchanged
        assert len(empty_queue) == 3
        assert empty_queue.dequeue() == p_crit
        assert len(empty_queue) == 2


class TestTriageQueueUS3:
    """Tests for User Story 3 (Triage Workload Statistics and Reporting)."""

    def test_statistics_empty_queue(self, empty_queue: TriageQueue) -> None:
        """Verify empty queue produces 0 for all statistics."""
        stats = empty_queue.get_statistics()
        assert stats.critical_count == 0
        assert stats.urgent_count == 0
        assert stats.standard_count == 0
        assert stats.total_count == 0

    def test_statistics_updates_on_enqueue_and_dequeue(
        self,
        empty_queue: TriageQueue,
        patient_factory: Callable[..., PatientRecord],
    ) -> None:
        """Verify stats accurately reflect counts per level through lifecycle."""
        # Enqueue: 2 Critical, 1 Urgent, 3 Standard
        empty_queue.enqueue(patient_factory(name="C1", triage_level=TriageLevel.CRITICAL))
        empty_queue.enqueue(patient_factory(name="C2", triage_level=TriageLevel.CRITICAL))
        empty_queue.enqueue(patient_factory(name="U1", triage_level=TriageLevel.URGENT))
        empty_queue.enqueue(patient_factory(name="S1", triage_level=TriageLevel.STANDARD))
        empty_queue.enqueue(patient_factory(name="S2", triage_level=TriageLevel.STANDARD))
        empty_queue.enqueue(patient_factory(name="S3", triage_level=TriageLevel.STANDARD))

        stats = empty_queue.get_statistics()
        assert stats.critical_count == 2
        assert stats.urgent_count == 1
        assert stats.standard_count == 3
        assert stats.total_count == 6

        # Peek does not affect stats
        empty_queue.peek()
        stats_after_peek = empty_queue.get_statistics()
        assert stats_after_peek == stats

        # Dequeue one critical patient
        dequeued = empty_queue.dequeue()
        assert dequeued is not None and dequeued.triage_level == TriageLevel.CRITICAL

        stats2 = empty_queue.get_statistics()
        assert stats2.critical_count == 1
        assert stats2.urgent_count == 1
        assert stats2.standard_count == 3
        assert stats2.total_count == 5

