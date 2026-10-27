"""End-to-end quickstart validation scenarios from specs/001-triage-queue-manager/quickstart.md."""

import io
from unittest.mock import patch
import pytest

from triage_queue import PatientRecord, TriageLevel, TriageQueue
from triage_queue.cli.menu import run_menu_loop


class TestQuickstartScenarios:
    """Validate all 4 scenarios documented in quickstart.md."""

    def test_scenario_a_out_of_order_multi_priority_intake_and_priority_dequeue(self) -> None:
        """Scenario A: Standard Bob (3), Urgent Jane (2), Critical Alice (1) -> Alice #1, Jane #2, Bob #3."""
        inputs = [
            "1\n", "Standard Patient Bob\n", "3\n",
            "1\n", "Urgent Patient Jane\n", "2\n",
            "1\n", "Critical Patient Alice\n", "1\n",
            "4\n",  # View queue
            "2\n",  # Call next -> Critical Alice
            "2\n",  # Call next -> Urgent Jane
            "2\n",  # Call next -> Standard Bob
            "6\n",  # Exit
        ]
        out = io.StringIO()
        with patch("sys.stdin", io.StringIO("".join(inputs))), patch("sys.stdout", out):
            code = run_menu_loop()

        assert code == 0
        output = out.getvalue()

        # In queue table, Alice must appear before Jane, and Jane before Bob
        table_start = output.find("#    ID        PRIORITY")
        assert table_start != -1

        alice_table_pos = output.find("Critical Patient Alice", table_start)
        jane_table_pos = output.find("Urgent Patient Jane", table_start)
        bob_table_pos = output.find("Standard Patient Bob", table_start)
        assert alice_table_pos != -1 and jane_table_pos != -1 and bob_table_pos != -1
        assert alice_table_pos < jane_table_pos < bob_table_pos

        # In dispatches, Alice called first, Jane second, Bob third
        dispatches_start = output.find("Total patients waiting: 3")
        disp_alice = output.find("Name:        Critical Patient Alice", dispatches_start)
        disp_jane = output.find("Name:        Urgent Patient Jane", dispatches_start)
        disp_bob = output.find("Name:        Standard Patient Bob", dispatches_start)
        assert disp_alice != -1 and disp_jane != -1 and disp_bob != -1
        assert disp_alice < disp_jane < disp_bob


    def test_scenario_b_peek_and_non_mutating_queue_inspection(self) -> None:
        """Scenario B: Register two patients, peek next patient, confirm total count remains 2."""
        inputs = [
            "1\n", "Patient Two\n", "2\n",
            "1\n", "Patient Three\n", "3\n",
            "3\n",  # Peek -> Patient Two
            "5\n",  # Stats -> Total Waiting: 2
            "6\n",  # Exit
        ]
        out = io.StringIO()
        with patch("sys.stdin", io.StringIO("".join(inputs))), patch("sys.stdout", out):
            code = run_menu_loop()

        assert code == 0
        output = out.getvalue()
        assert "[PEEK] Next patient in line (remains queued):" in output
        assert "Name:        Patient Two" in output
        assert "Total Waiting:           2" in output

    def test_scenario_c_empty_queue_graceful_handling(self) -> None:
        """Scenario C: Call next (2), peek (3), view stats (5) on empty queue with zero crashes."""
        inputs = [
            "2\n",  # Call next on empty
            "3\n",  # Peek on empty
            "5\n",  # Stats on empty
            "6\n",  # Exit
        ]
        out = io.StringIO()
        with patch("sys.stdin", io.StringIO("".join(inputs))), patch("sys.stdout", out):
            code = run_menu_loop()

        assert code == 0
        output = out.getvalue()
        assert "[INFO] The triage queue is currently empty. No patients waiting." in output
        assert "Level 1 (Critical):      0" in output
        assert "Total Waiting:           0" in output

    def test_scenario_d_resilient_input_validation(self) -> None:
        """Scenario D: Blank name reprompts, invalid level reprompts, invalid menu choice reprompts, exit cleanly."""
        inputs = [
            "1\n",
            "\n",  # Blank name -> error
            "Valid Patient Name\n",
            "9\n",  # Invalid level -> error
            "abc\n",  # Invalid level -> error
            "2\n",  # Valid level 2
            "invalid_choice\n",  # Unrecognized menu selection -> error
            "6\n",  # Clean exit
        ]
        out = io.StringIO()
        with patch("sys.stdin", io.StringIO("".join(inputs))), patch("sys.stdout", out):
            code = run_menu_loop()

        assert code == 0
        output = out.getvalue()
        assert "[ERROR] Patient name cannot be blank. Please enter a valid name." in output
        assert "[ERROR] Invalid triage level '9'." in output
        assert "[ERROR] Invalid triage level 'abc'." in output
        assert "[SUCCESS] Patient successfully admitted:" in output
        assert "[ERROR] Unrecognized selection 'invalid_choice'." in output
        assert "Exiting Emergency Unit Triage Queue Manager. Goodbye." in output
