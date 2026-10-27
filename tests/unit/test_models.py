"""Unit tests for TriageLevel and PatientRecord domain models."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import pytest

from triage_queue.exceptions import EmptyNameError, InvalidTriageLevelError
from triage_queue.models import PatientRecord, TriageLevel


class TestTriageLevel:
    """Tests for the TriageLevel IntEnum."""

    def test_enum_values_and_ordering(self) -> None:
        """Verify enum values and natural integer ordering."""
        assert TriageLevel.CRITICAL.value == 1
        assert TriageLevel.URGENT.value == 2
        assert TriageLevel.STANDARD.value == 3
        assert TriageLevel.CRITICAL < TriageLevel.URGENT < TriageLevel.STANDARD

    def test_labels(self) -> None:
        """Verify human-readable label property."""
        assert TriageLevel.CRITICAL.label == "Critical"
        assert TriageLevel.URGENT.label == "Urgent"
        assert TriageLevel.STANDARD.label == "Standard"

    @pytest.mark.parametrize(
        ("raw_val", "expected"),
        [
            (1, TriageLevel.CRITICAL),
            (2, TriageLevel.URGENT),
            (3, TriageLevel.STANDARD),
            ("1", TriageLevel.CRITICAL),
            ("2", TriageLevel.URGENT),
            ("3", TriageLevel.STANDARD),
            (" 1 ", TriageLevel.CRITICAL),
        ],
    )
    def test_from_value_success(self, raw_val: int | str, expected: TriageLevel) -> None:
        """Verify from_value correctly parses integers and string representations."""
        assert TriageLevel.from_value(raw_val) == expected

    @pytest.mark.parametrize("invalid_val", [0, 4, -1, 99, "0", "4", "abc", "", None, 3.14])
    def test_from_value_invalid_raises_error(self, invalid_val: object) -> None:
        """Verify from_value raises InvalidTriageLevelError for invalid input."""
        with pytest.raises(InvalidTriageLevelError):
            TriageLevel.from_value(invalid_val)  # type: ignore[arg-type]


class TestPatientRecord:
    """Tests for PatientRecord creation, validation, and immutability."""

    def test_create_valid_patient(self) -> None:
        """Verify creating a valid patient with explicit attributes."""
        dt = datetime(2026, 10, 27, 12, 0, 0, tzinfo=timezone.utc)
        record = PatientRecord.create(
            name="Jane Doe",
            triage_level=TriageLevel.URGENT,
            arrived_at=dt,
            patient_id="PT-1001",
        )
        assert record.id == "PT-1001"
        assert record.name == "Jane Doe"
        assert record.triage_level == TriageLevel.URGENT
        assert record.arrived_at == dt

    def test_create_with_integer_triage_level(self) -> None:
        """Verify triage level can be provided as integer."""
        record = PatientRecord.create(name="Jane Doe", triage_level=1)
        assert record.triage_level == TriageLevel.CRITICAL

    def test_name_whitespace_stripped(self) -> None:
        """Verify leading and trailing whitespace is stripped from patient name."""
        record = PatientRecord.create(name="   John Smith   ", triage_level=3)
        assert record.name == "John Smith"

    @pytest.mark.parametrize("empty_name", ["", "   ", "\t\n", None])
    def test_empty_or_whitespace_name_raises_error(self, empty_name: object) -> None:
        """Verify empty or whitespace-only name raises EmptyNameError."""
        with pytest.raises(EmptyNameError):
            PatientRecord.create(name=empty_name, triage_level=2)  # type: ignore[arg-type]

    def test_invalid_triage_level_raises_error(self) -> None:
        """Verify invalid triage level raises InvalidTriageLevelError."""
        with pytest.raises(InvalidTriageLevelError):
            PatientRecord.create(name="Alice", triage_level=9)

    def test_default_id_and_timestamp(self) -> None:
        """Verify default UUID or formatted ID and timezone-aware arrived_at timestamp are assigned."""
        record = PatientRecord.create(name="Alice", triage_level=1)
        assert record.id
        assert isinstance(record.arrived_at, datetime)
        assert record.arrived_at.tzinfo is not None

    def test_immutability(self) -> None:
        """Verify PatientRecord is frozen and raises FrozenInstanceError on modification."""
        record = PatientRecord.create(name="Immutable Patient", triage_level=1)
        with pytest.raises(FrozenInstanceError):
            record.name = "Modified Name"  # type: ignore[misc]
        with pytest.raises(FrozenInstanceError):
            record.triage_level = TriageLevel.STANDARD  # type: ignore[misc]
