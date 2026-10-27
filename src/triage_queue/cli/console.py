"""Terminal formatting and tabular display helpers."""

from typing import Sequence

from triage_queue.models import PatientRecord, QueueStatistics


def format_patient_details(patient: PatientRecord, prefix: str) -> str:
    """Format single patient details for display."""
    arrival_str = patient.arrived_at.strftime("%Y-%m-%d %H:%M:%S")
    severity_str = f"Level {patient.triage_level.value} ({patient.triage_level.label})"
    return (
        f"{prefix}\n"
        f"  ID:          {patient.id}\n"
        f"  Name:        {patient.name}\n"
        f"  Severity:    {severity_str}\n"
        f"  Arrival:     {arrival_str}"
    )


def format_queue_table(patients: Sequence[PatientRecord]) -> str:
    """Format sequence of waiting patients as an aligned terminal table."""
    if not patients:
        return "[INFO] The triage queue is currently empty. No patients waiting."

    sep = "=" * 80
    header = "#    ID        PRIORITY               NAME                  ARRIVAL TIME"
    lines = [sep, header, sep]

    for idx, patient in enumerate(patients, start=1):
        idx_str = f"{idx:<5}"
        id_str = f"{patient.id:<10}"
        priority_str = f"Level {patient.triage_level.value} ({patient.triage_level.label}):<23"
        priority_formatted = f"Level {patient.triage_level.value} ({patient.triage_level.label})"
        priority_padded = f"{priority_formatted:<23}"
        name_str = f"{patient.name:<22}"
        arrival_str = patient.arrived_at.strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"{idx_str}{id_str}{priority_padded}{name_str}{arrival_str}")

    lines.append(sep)
    lines.append(f"Total patients waiting: {len(patients)}")
    return "\n".join(lines)


def format_statistics(stats: QueueStatistics) -> str:
    """Format triage statistics summary card."""
    sep = "=" * 40
    divider = "-" * 40
    lines = [
        sep,
        "       TRIAGE WORKLOAD STATISTICS",
        sep,
        f"  Level 1 (Critical):      {stats.critical_count}",
        f"  Level 2 (Urgent):        {stats.urgent_count}",
        f"  Level 3 (Standard):      {stats.standard_count}",
        divider,
        f"  Total Waiting:           {stats.total_count}",
        sep,
    ]
    return "\n".join(lines)
