"""Interactive menu loop and resilient input dialogs for triage queue management."""

import sys
from typing import Optional

from triage_queue.cli.console import (
    format_patient_details,
    format_queue_table,
    format_statistics,
)
from triage_queue.exceptions import EmptyNameError, InvalidTriageLevelError
from triage_queue.models import PatientRecord, TriageLevel
from triage_queue.queue import TriageQueue

MENU_HEADER = """==================================================
   EMERGENCY UNIT TRIAGE QUEUE MANAGER
==================================================
1. Register New Patient (Intake)
2. Call Next Patient for Service (Dequeue)
3. Peek Next Patient in Line
4. View Current Triage Queue
5. View Triage Workload Statistics
6. Exit System
--------------------------------------------------"""


def prompt_patient_name() -> str:
    """Prompt for patient name with resilient retry loop."""
    while True:
        try:
            name = input("Enter Patient Name: ")
        except (EOFError, KeyboardInterrupt):
            raise
        cleaned = name.strip()
        if not cleaned:
            print("[ERROR] Patient name cannot be blank. Please enter a valid name.")
            continue
        return cleaned


def prompt_triage_level() -> TriageLevel:
    """Prompt for triage level with resilient retry loop."""
    prompt_text = "Enter Triage Level (1=Critical, 2=Urgent, 3=Standard): "
    while True:
        try:
            raw_input = input(prompt_text)
        except (EOFError, KeyboardInterrupt):
            raise
        try:
            return TriageLevel.from_value(raw_input)
        except InvalidTriageLevelError:
            print(
                f"[ERROR] Invalid triage level '{raw_input.strip()}'. "
                f"Must be 1 (Critical), 2 (Urgent), or 3 (Standard)."
            )


def handle_patient_intake(queue: TriageQueue) -> None:
    """Guide the user through patient intake registration."""
    print("--- Patient Intake ---")
    name = prompt_patient_name()
    level = prompt_triage_level()
    patient = PatientRecord.create(name=name, triage_level=level)
    queue.enqueue(patient)
    print(format_patient_details(patient, prefix="[SUCCESS] Patient successfully admitted:"))


def handle_call_next_patient(queue: TriageQueue) -> None:
    """Dequeue and display the highest priority patient."""
    patient = queue.dequeue()
    if patient is None:
        print("[INFO] The triage queue is currently empty. No patients waiting.")
    else:
        print(format_patient_details(patient, prefix="[DISPATCH] Calling next patient for care:"))


def handle_peek_next_patient(queue: TriageQueue) -> None:
    """Peek and display the next patient in line without removing them."""
    patient = queue.peek()
    if patient is None:
        print("[INFO] The triage queue is currently empty. No patients waiting.")
    else:
        print(format_patient_details(patient, prefix="[PEEK] Next patient in line (remains queued):"))


def handle_view_queue(queue: TriageQueue) -> None:
    """Display the full active queue table."""
    print(format_queue_table(queue.list_all()))


def handle_view_statistics(queue: TriageQueue) -> None:
    """Display current triage workload statistics card."""
    print(format_statistics(queue.get_statistics()))


def run_menu_loop(queue: Optional[TriageQueue] = None) -> int:
    """Run interactive terminal menu loop until exit option is selected."""
    active_queue = queue if queue is not None else TriageQueue()

    while True:
        print(MENU_HEADER)
        try:
            choice = input("Select an option (1-6): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting Emergency Unit Triage Queue Manager. Goodbye.")
            return 0

        if choice == "1":
            handle_patient_intake(active_queue)
        elif choice == "2":
            handle_call_next_patient(active_queue)
        elif choice == "3":
            handle_peek_next_patient(active_queue)
        elif choice == "4":
            handle_view_queue(active_queue)
        elif choice == "5":
            handle_view_statistics(active_queue)
        elif choice == "6":
            print("Exiting Emergency Unit Triage Queue Manager. Goodbye.")
            return 0
        else:
            print(f"[ERROR] Unrecognized selection '{choice}'. Please enter a number between 1 and 6.")
