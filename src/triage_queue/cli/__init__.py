"""CLI interface for Emergency Unit Triage Queue Manager."""

from triage_queue.cli.console import (
    format_patient_details,
    format_queue_table,
    format_statistics,
)
from triage_queue.cli.menu import run_menu_loop

__all__ = [
    "format_patient_details",
    "format_queue_table",
    "format_statistics",
    "run_menu_loop",
]
