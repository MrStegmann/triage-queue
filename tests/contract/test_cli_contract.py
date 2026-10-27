"""Contract tests for terminal console interface matching specs/001-triage-queue-manager/contracts/cli-contract.md."""

import io
from unittest.mock import patch
import pytest

from triage_queue import PatientRecord, TriageLevel, TriageQueue
from triage_queue.cli.console import format_patient_details, format_queue_table, format_statistics
from triage_queue.cli.menu import run_menu_loop


class TestCLIFormattingContract:
    """Tests verifying output formatting matches CLI contract specifications."""

    def test_format_patient_details(self) -> None:
        """Verify format_patient_details layout matches contract."""
        p = PatientRecord.create(
            name="John Doe",
            triage_level=TriageLevel.CRITICAL,
            patient_id="PT-1001",
        )
        formatted = format_patient_details(p, prefix="[SUCCESS] Patient successfully admitted:")
        assert "[SUCCESS] Patient successfully admitted:" in formatted
        assert "ID:          PT-1001" in formatted
        assert "Name:        John Doe" in formatted
        assert "Severity:    Level 1 (Critical)" in formatted
        assert "Arrival:     " in formatted

    def test_format_queue_table_empty(self) -> None:
        """Verify format_queue_table on empty queue returns notice."""
        queue = TriageQueue()
        output = format_queue_table(queue.list_all())
        assert "[INFO] The triage queue is currently empty. No patients waiting." in output

    def test_format_queue_table_populated(self) -> None:
        """Verify format_queue_table header and patient rows."""
        queue = TriageQueue()
        queue.enqueue(PatientRecord.create(name="Critical Alice", triage_level=1, patient_id="PT-001"))
        queue.enqueue(PatientRecord.create(name="Standard Bob", triage_level=3, patient_id="PT-002"))

        table = format_queue_table(queue.list_all())
        assert "#    ID        PRIORITY               NAME                  ARRIVAL TIME" in table
        assert "PT-001" in table
        assert "Critical Alice" in table
        assert "Level 1 (Critical)" in table
        assert "PT-002" in table
        assert "Standard Bob" in table
        assert "Total patients waiting: 2" in table

    def test_format_statistics(self) -> None:
        """Verify format_statistics matches contract layout."""
        queue = TriageQueue()
        queue.enqueue(PatientRecord.create(name="Crit 1", triage_level=1))
        queue.enqueue(PatientRecord.create(name="Urg 1", triage_level=2))
        queue.enqueue(PatientRecord.create(name="Std 1", triage_level=3))

        stats_output = format_statistics(queue.get_statistics())
        assert "TRIAGE WORKLOAD STATISTICS" in stats_output
        assert "Level 1 (Critical):      1" in stats_output
        assert "Level 2 (Urgent):        1" in stats_output
        assert "Level 3 (Standard):      1" in stats_output
        assert "Total Waiting:           3" in stats_output


class TestCLIMenuLoopContract:
    """Tests verifying interactive menu loop against simulated stdin inputs."""

    def test_menu_exit_immediately(self) -> None:
        """Verify selecting option 6 exits cleanly."""
        inputs = ["6\n"]
        out = io.StringIO()
        queue = TriageQueue()

        with patch("sys.stdin", io.StringIO("".join(inputs))), patch("sys.stdout", out):
            exit_code = run_menu_loop(queue)

        assert exit_code == 0
        output = out.getvalue()
        assert "EMERGENCY UNIT TRIAGE QUEUE MANAGER" in output
        assert "Exiting Emergency Unit Triage Queue Manager. Goodbye." in output

    def test_menu_intake_validation_and_registration(self) -> None:
        """Verify input validation loops: blank name reprompt, invalid level reprompt, then success."""
        # 1 -> intake; "" (blank name error) -> "John Doe"; "invalid" (error) -> "1"; 6 -> exit
        inputs = ["1\n", "\n", "John Doe\n", "abc\n", "9\n", "1\n", "6\n"]
        out = io.StringIO()
        queue = TriageQueue()

        with patch("sys.stdin", io.StringIO("".join(inputs))), patch("sys.stdout", out):
            run_menu_loop(queue)

        output = out.getvalue()
        assert "[ERROR] Patient name cannot be blank. Please enter a valid name." in output
        assert "[ERROR] Invalid triage level 'abc'. Must be 1 (Critical), 2 (Urgent), or 3 (Standard)." in output
        assert "[ERROR] Invalid triage level '9'. Must be 1 (Critical), 2 (Urgent), or 3 (Standard)." in output
        assert "[SUCCESS] Patient successfully admitted:" in output
        assert "John Doe" in output
        assert len(queue) == 1

    def test_menu_empty_queue_operations(self) -> None:
        """Verify dequeue (2), peek (3), view queue (4) on empty queue show informative message."""
        inputs = ["2\n", "3\n", "4\n", "5\n", "6\n"]
        out = io.StringIO()
        queue = TriageQueue()

        with patch("sys.stdin", io.StringIO("".join(inputs))), patch("sys.stdout", out):
            run_menu_loop(queue)

        output = out.getvalue()
        assert "[INFO] The triage queue is currently empty. No patients waiting." in output
        assert "TRIAGE WORKLOAD STATISTICS" in output
        assert "Total Waiting:           0" in output

    def test_menu_unrecognized_selection(self) -> None:
        """Verify entering unknown option reprompts without error."""
        inputs = ["9\n", "invalid\n", "6\n"]
        out = io.StringIO()
        queue = TriageQueue()

        with patch("sys.stdin", io.StringIO("".join(inputs))), patch("sys.stdout", out):
            run_menu_loop(queue)

        output = out.getvalue()
        assert "[ERROR] Unrecognized selection '9'. Please enter a number between 1 and 6." in output
        assert "[ERROR] Unrecognized selection 'invalid'. Please enter a number between 1 and 6." in output
