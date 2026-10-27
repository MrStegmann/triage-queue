"""Contract tests verifying TriageQueue against specs/001-triage-queue-manager/contracts/queue-api.md."""

from datetime import datetime, timezone
import pytest

from triage_queue.exceptions import EmptyNameError, InvalidTriageLevelError, TriageQueueError, ValidationError
from triage_queue.models import PatientRecord, TriageLevel
from triage_queue.queue import TriageQueue


class TestQueueAPIContractUS1:
    """Verifies API contract adherence for User Story 1 (enqueue, dequeue, exceptions)."""

    def test_exception_inheritance_contract(self) -> None:
        """Verify exception hierarchy matches contract: EmptyNameError and InvalidTriageLevelError are ValidationErrors."""
        assert issubclass(ValidationError, TriageQueueError)
        assert issubclass(EmptyNameError, ValidationError)
        assert issubclass(InvalidTriageLevelError, ValidationError)

    def test_patient_record_factory_contract(self) -> None:
        """Verify PatientRecord.create contract signature and behavior."""
        now = datetime.now(timezone.utc)
        record = PatientRecord.create(
            name="Contract Patient",
            triage_level=1,
            arrived_at=now,
            patient_id="PT-SPEC-1",
        )
        assert record.id == "PT-SPEC-1"
        assert record.name == "Contract Patient"
        assert record.triage_level == TriageLevel.CRITICAL
        assert record.arrived_at == now

    def test_queue_enqueue_dequeue_contract(self) -> None:
        """Verify TriageQueue methods enqueue, dequeue, is_empty, __len__ contract."""
        queue = TriageQueue()
        assert queue.is_empty() is True
        assert len(queue) == 0
        assert queue.dequeue() is None

        p = PatientRecord.create(name="Patient One", triage_level=TriageLevel.URGENT)
        queue.enqueue(p)

        assert queue.is_empty() is False
        assert len(queue) == 1

        result = queue.dequeue()
        assert result is p
        assert queue.is_empty() is True


class TestQueueAPIContractUS2:
    """Verifies API contract adherence for User Story 2 (peek, list_all)."""

    def test_peek_and_list_all_contract(self) -> None:
        """Verify peek() and list_all() return types and signatures."""
        queue = TriageQueue()
        # Empty
        assert queue.peek() is None
        assert queue.list_all() == ()

        p1 = PatientRecord.create(name="Patient One", triage_level=TriageLevel.URGENT)
        p2 = PatientRecord.create(name="Patient Two", triage_level=TriageLevel.CRITICAL)
        queue.enqueue(p1)
        queue.enqueue(p2)

        peek_result = queue.peek()
        assert peek_result is p2

        listing = queue.list_all()
        assert isinstance(listing, (tuple, list))
        assert list(listing) == [p2, p1]


class TestQueueAPIContractUS3:
    """Verifies API contract adherence for User Story 3 (QueueStatistics, get_statistics)."""

    def test_statistics_schema_and_types(self) -> None:
        """Verify QueueStatistics fields, types, and immutability."""
        from triage_queue.models import QueueStatistics
        from dataclasses import FrozenInstanceError

        stats = QueueStatistics(critical_count=1, urgent_count=2, standard_count=3, total_count=6)
        assert stats.critical_count == 1
        assert stats.urgent_count == 2
        assert stats.standard_count == 3
        assert stats.total_count == 6

        with pytest.raises(FrozenInstanceError):
            stats.critical_count = 5  # type: ignore[misc]

    def test_queue_get_statistics_contract(self) -> None:
        """Verify queue.get_statistics() returns a QueueStatistics instance."""
        from triage_queue.models import QueueStatistics

        queue = TriageQueue()
        stats = queue.get_statistics()
        assert isinstance(stats, QueueStatistics)
        assert stats.total_count == 0


