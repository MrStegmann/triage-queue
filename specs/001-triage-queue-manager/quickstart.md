# Quickstart & End-to-End Validation Guide

**Feature**: Emergency Unit Triage Queue Manager  
**Branch**: `001-triage-queue-manager`  
**Status**: Completed  

This guide provides step-by-step instructions for running and validating the Emergency Unit Triage Queue Manager.

---

## 1. Prerequisites & Environment

- **Python**: Version 3.12 or later (verified runtime: Python 3.14.7).
- **Dependencies**: None (uses standard Python runtime libraries).
- **Test Runner**: `pytest` (optional, for automated test suite execution).

---

## 2. Automated Test Suite Execution

Run the complete test suite verifying unit, integration, and contract test suites:

```bash
# Execute all tests with concise reporting
python -m pytest

# Execute with detailed verbose output
python -m pytest -v
```

Expected Outcome:
- All unit tests covering `PatientRecord`, `TriageLevel`, and `TriageQueue` pass.
- Edge case tests (empty queue peek/dequeue, timestamp collisions, invalid triage levels) pass.
- CLI contract tests verifying input parsing and error recovery pass.

---

## 3. Interactive Validation Scenarios

Launch the interactive console application:

```bash
python src/triage_queue/cli/main.py
```

### Scenario A: Out-of-Order Multi-Priority Intake & Priority Dequeue
*Validates User Story 1 (P1) & FR-002 / FR-003*

1. Choose Option `1` (Intake).
   - Enter Name: `Standard Patient Bob`
   - Enter Triage Level: `3` (Standard)
2. Choose Option `1` (Intake).
   - Enter Name: `Urgent Patient Jane`
   - Enter Triage Level: `2` (Urgent)
3. Choose Option `1` (Intake).
   - Enter Name: `Critical Patient Alice`
   - Enter Triage Level: `1` (Critical)
4. Choose Option `4` (View Current Triage Queue).
   - **Expected Outcome**: The queue listing shows `Critical Patient Alice` at #1, `Urgent Patient Jane` at #2, and `Standard Patient Bob` at #3, despite Alice arriving last.
5. Choose Option `2` (Call Next Patient).
   - **Expected Outcome**: `Critical Patient Alice` is called first.
6. Choose Option `2` (Call Next Patient).
   - **Expected Outcome**: `Urgent Patient Jane` is called second.
7. Choose Option `2` (Call Next Patient).
   - **Expected Outcome**: `Standard Patient Bob` is called third.

---

### Scenario B: Queue Peek and Non-Mutating Queue Inspection
*Validates User Story 2 (P2) & FR-006 / FR-008*

1. Register two patients (e.g. Level 2 and Level 3).
2. Choose Option `3` (Peek Next Patient).
   - **Expected Outcome**: Displays the Level 2 patient without modifying the queue.
3. Choose Option `5` (View Triage Workload Statistics).
   - **Expected Outcome**: Confirms total waiting count remains 2 (peek did not decrement the queue).

---

### Scenario C: Empty Queue Graceful Handling
*Validates User Story 1 Acceptance Scenario 4 & FR-007*

1. Start with an empty queue (or dequeue all admitted patients).
2. Choose Option `2` (Call Next Patient).
   - **Expected Outcome**: System displays: `[INFO] The triage queue is currently empty. No patients waiting.` No crash or exception occurs.
3. Choose Option `3` (Peek Next Patient).
   - **Expected Outcome**: System displays empty queue message without error.
4. Choose Option `5` (View Statistics).
   - **Expected Outcome**: Displays 0 counts across all levels with 0 total waiting.

---

### Scenario D: Resilient Input Validation
*Validates User Story 4 (P4) & FR-011*

1. Choose Option `1` (Intake).
2. At `Enter Patient Name:`, press Enter without typing anything (blank).
   - **Expected Outcome**: System reports `[ERROR] Patient name cannot be blank` and re-prompts for name without exiting.
3. Enter `Valid Patient Name`.
4. At `Enter Triage Level:`, enter `9` or `abc`.
   - **Expected Outcome**: System reports `[ERROR] Invalid triage level` and re-prompts for triage level.
5. Enter `2`.
   - **Expected Outcome**: Patient is admitted successfully.
6. At the main menu, enter `invalid_choice`.
   - **Expected Outcome**: System warns of unrecognized option and displays menu cleanly.
7. Choose Option `6` to exit cleanly.

---

## 4. References

- Data Model: [data-model.md](file:///j:/GitHub/triage-queue/specs/001-triage-queue-manager/data-model.md)
- Core Library Contract: [contracts/queue-api.md](file:///j:/GitHub/triage-queue/specs/001-triage-queue-manager/contracts/queue-api.md)
- Terminal Interface Contract: [contracts/cli-contract.md](file:///j:/GitHub/triage-queue/specs/001-triage-queue-manager/contracts/cli-contract.md)
