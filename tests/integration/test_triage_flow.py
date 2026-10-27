"""Integration tests for end-to-end triage admission and dispatch flow."""

from datetime import datetime, timezone, timedelta
import pytest

from triage_queue import PatientRecord, TriageLevel, TriageQueue


class TestTriageFlowLifecycleUS1:
    """End-to-end integration tests for patient admission and priority service dispatch."""

    def test_full_intake_and_dispatch_lifecycle(self) -> None:
        """Simulate realistic emergency intake shift with out-of-order arrivals and priority dispatch."""
        queue = TriageQueue()
        base = datetime(2026, 10, 27, 8, 0, 0, tzinfo=timezone.utc)

        # 1. Patient arrives with non-urgent cough (Standard)
        p1 = PatientRecord.create(
            name="Bob Standard",
            triage_level=TriageLevel.STANDARD,
            arrived_at=base,
            patient_id="PT-001",
        )
        queue.enqueue(p1)

        # 2. Patient arrives with severe abdominal pain (Urgent)
        p2 = PatientRecord.create(
            name="Jane Urgent",
            triage_level=TriageLevel.URGENT,
            arrived_at=base + timedelta(minutes=5),
            patient_id="PT-002",
        )
        queue.enqueue(p2)

        # 3. Patient arrives via ambulance in cardiac arrest (Critical)
        p3 = PatientRecord.create(
            name="Alice Critical",
            triage_level=TriageLevel.CRITICAL,
            arrived_at=base + timedelta(minutes=10),
            patient_id="PT-003",
        )
        queue.enqueue(p3)

        # 4. Another urgent patient arrives (fracture)
        p4 = PatientRecord.create(
            name="Charlie Urgent",
            triage_level=TriageLevel.URGENT,
            arrived_at=base + timedelta(minutes=15),
            patient_id="PT-004",
        )
        queue.enqueue(p4)

        assert len(queue) == 4

        # Doctor calls next patient -> Must be Alice (Critical)
        c1 = queue.dequeue()
        assert c1 is not None
        assert c1.id == "PT-003"
        assert c1.name == "Alice Critical"

        # Doctor calls next patient -> Must be Jane (Urgent first arrival)
        c2 = queue.dequeue()
        assert c2 is not None
        assert c2.id == "PT-002"
        assert c2.name == "Jane Urgent"

        # Doctor calls next patient -> Must be Charlie (Urgent second arrival)
        c3 = queue.dequeue()
        assert c3 is not None
        assert c3.id == "PT-004"
        assert c3.name == "Charlie Urgent"

        # Doctor calls next patient -> Must be Bob (Standard)
        c4 = queue.dequeue()
        assert c4 is not None
        assert c4.id == "PT-001"
        assert c4.name == "Bob Standard"

        # Queue is now empty
        assert queue.is_empty()
        assert queue.dequeue() is None


class TestTriageFlowInspectionUS2:
    """Integration test verifying peek and queue listing preserve queue immutability."""

    def test_inspection_preserves_queue_immutability(self) -> None:
        """Verify inspecting queue via peek and list_all does not alter order or count during clinical operations."""
        queue = TriageQueue()
        p1 = PatientRecord.create(name="Standard Patient", triage_level=TriageLevel.STANDARD)
        p2 = PatientRecord.create(name="Urgent Patient", triage_level=TriageLevel.URGENT)

        queue.enqueue(p1)
        queue.enqueue(p2)

        # Active queue count is 2
        assert len(queue) == 2

        # Peek multiple times
        assert queue.peek() == p2
        assert queue.peek() == p2
        assert len(queue) == 2

        # List all patients
        listing = queue.list_all()
        assert len(listing) == 2
        assert listing[0] == p2
        assert listing[1] == p1

        # Still 2 patients in queue
        assert len(queue) == 2

        # Now dequeue
        assert queue.dequeue() == p2
        assert len(queue) == 1

        # Peek now reveals p1
        assert queue.peek() == p1
        assert queue.list_all() == (p1,)


class TestTriageFlowStatisticsUS3:
    """Integration test verifying real-time statistics updates across triage lifecycle."""

    def test_statistics_lifecycle_surge_and_recovery(self) -> None:
        """Verify statistics accurately track a surge of mixed arrivals and subsequent discharges."""
        queue = TriageQueue()
        s0 = queue.get_statistics()
        assert s0.total_count == 0

        # Surge arrival: 3 Critical, 2 Urgent, 4 Standard
        for i in range(3):
            queue.enqueue(PatientRecord.create(name=f"Crit {i}", triage_level=TriageLevel.CRITICAL))
        for i in range(2):
            queue.enqueue(PatientRecord.create(name=f"Urg {i}", triage_level=TriageLevel.URGENT))
        for i in range(4):
            queue.enqueue(PatientRecord.create(name=f"Std {i}", triage_level=TriageLevel.STANDARD))

        s1 = queue.get_statistics()
        assert s1.critical_count == 3
        assert s1.urgent_count == 2
        assert s1.standard_count == 4
        assert s1.total_count == 9

        # Process all critical patients
        for _ in range(3):
            c = queue.dequeue()
            assert c is not None and c.triage_level == TriageLevel.CRITICAL

        s2 = queue.get_statistics()
        assert s2.critical_count == 0
        assert s2.urgent_count == 2
        assert s2.standard_count == 4
        assert s2.total_count == 6

        # Process rest of queue
        while not queue.is_empty():
            queue.dequeue()

        s3 = queue.get_statistics()
        assert s3.critical_count == 0
        assert s3.urgent_count == 0
        assert s3.standard_count == 0
        assert s3.total_count == 0


class TestFullTerminalSessionWorkflowUS4:
    """Integration test verifying full terminal session end-to-end workflow."""

    def test_complete_interactive_session_lifecycle(self) -> None:
        """Simulate a complete staff session from launch to shutdown."""
        import io
        from unittest.mock import patch
        from triage_queue.cli.menu import run_menu_loop

        # Inputs:
        # 2 (dequeue empty)
        # 3 (peek empty)
        # 1 (intake: "Bob Standard", 3)
        # 1 (intake: "Jane Urgent", 2)
        # 1 (intake: "Alice Critical", 1)
        # 3 (peek -> Alice)
        # 4 (view queue)
        # 5 (view stats -> 3 total)
        # 2 (call next -> Alice)
        # 2 (call next -> Jane)
        # 5 (view stats -> 1 total)
        # 6 (exit)
        session_inputs = [
            "2\n",
            "3\n",
            "1\n", "Bob Standard\n", "3\n",
            "1\n", "Jane Urgent\n", "2\n",
            "1\n", "Alice Critical\n", "1\n",
            "3\n",
            "4\n",
            "5\n",
            "2\n",
            "2\n",
            "5\n",
            "6\n",
        ]
        out = io.StringIO()
        with patch("sys.stdin", io.StringIO("".join(session_inputs))), patch("sys.stdout", out):
            code = run_menu_loop()

        assert code == 0
        transcript = out.getvalue()

        # Check empty warnings
        assert "[INFO] The triage queue is currently empty" in transcript

        # Check registrations
        assert "[SUCCESS] Patient successfully admitted:" in transcript
        assert "Bob Standard" in transcript
        assert "Jane Urgent" in transcript
        assert "Alice Critical" in transcript

        # Check peek
        assert "[PEEK] Next patient in line (remains queued):" in transcript

        # Check table
        assert "Total patients waiting: 3" in transcript

        # Check dispatches
        assert "[DISPATCH] Calling next patient for care:" in transcript

        # Check clean exit
        assert "Exiting Emergency Unit Triage Queue Manager. Goodbye." in transcript



