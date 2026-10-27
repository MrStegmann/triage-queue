# Feature Specification: Emergency Unit Triage Queue Manager

**Feature Branch**: `001-triage-queue-manager`

**Created**: 2026-10-27

**Status**: Ready for Planning

**Input**: User description: "Build a robust, terminal-based Python triage queue manager to replace a manual, error-prone emergency unit intake whiteboard. The system must correctly model a multi-priority queue with deterministic ordering, serving as the core backend scheduling component for a future larger application."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Patient Intake and Prioritized Service Call (Priority: P1)

As an emergency unit intake coordinator or triage nurse, I want to record newly arrived patients with their clinical triage severity and retrieve the highest-priority patient next, so that patients with critical, life-threatening conditions receive care before urgent or standard cases, regardless of arrival order.

**Why this priority**: Correct priority scheduling is the essential core mission of an emergency triage system. Without reliable prioritized intake and dequeueing, life-critical patients risk delayed care.

**Independent Test**: Can be tested end-to-end by adding three patients of varying severity (e.g., Level 3 standard, Level 2 urgent, Level 1 critical) in arbitrary order and verifying that consecutive service calls always dispatch Level 1 first, Level 2 second, and Level 3 last.

**Acceptance Scenarios**:

1. **Given** an empty triage queue, **When** a critical patient (Level 1) is registered, **Then** calling for the next patient immediately retrieves this critical patient.
2. **Given** existing waiting patients with Level 2 (Urgent) and Level 3 (Standard) status, **When** a new Level 1 (Critical) patient arrives and is registered, **Then** the next patient call returns the newly arrived Level 1 patient ahead of the earlier Level 2 and Level 3 patients.
3. **Given** multiple patients registered with the exact same triage severity level, **When** patient calls are made, **Then** patients within that severity level are retrieved strictly in First-In, First-Out (FIFO) arrival order.
4. **Given** an empty queue, **When** clinical staff attempts to call the next patient, **Then** the system gracefully notifies the user that no patients are waiting and does not terminate or enter an invalid state.

---

### User Story 2 - Queue Inspection and Queue Visibility (Priority: P2)

As an emergency department charge nurse or intake clerk, I want to inspect the next patient in line without removing them, and view the entire waiting list in attention sequence, so that staff have full situational awareness of pending patient load and upcoming arrivals.

**Why this priority**: Operational coordination requires visibility into who is next and how many patients are ahead in line without altering queue state or accidentally discharging patients from the queue.

**Independent Test**: Can be tested by adding multiple patients across different triage levels, viewing the ordered queue to verify the displayed order matches priority and arrival rules, and peeking the next patient to verify the queue length and contents remain unaltered.

**Acceptance Scenarios**:

1. **Given** an active queue with multiple waiting patients, **When** staff requests to peek at the next patient, **Then** the system displays the patient details (name, triage level, arrival timestamp) while keeping them in the queue.
2. **Given** an empty queue, **When** staff peeks at the next patient, **Then** the system reports that the queue is empty without errors or state modification.
3. **Given** an active queue with patients across diverse triage tiers, **When** staff requests to view the full queue, **Then** all waiting patients are presented sequentially in the exact chronological order in which they will be called for service.

---

### User Story 3 - Triage Workload Statistics and Reporting (Priority: P3)

As a hospital emergency supervisor or clinical lead, I want to see aggregate summary statistics of waiting patients categorized by triage level, so that I can assess departmental load and allocate clinical resources effectively.

**Why this priority**: Aggregated counts per triage tier provide vital operational intelligence for surge management and staffing decisions.

**Independent Test**: Can be tested by registering known counts of patients across Levels 1, 2, and 3, requesting the statistics report, and confirming that reported counts per tier and overall totals match actual waiting counts.

**Acceptance Scenarios**:

1. **Given** a queue containing 2 Level 1 patients, 3 Level 2 patients, and 5 Level 3 patients, **When** staff requests queue statistics, **Then** the system reports exact counts for each individual triage level.
2. **Given** an empty queue, **When** staff requests queue statistics, **Then** the system displays zero counts across all triage levels without errors.
3. **Given** an active queue, **When** a patient is called and removed from the queue, **Then** subsequent statistics immediately reflect the decremented count for that patient's triage tier.

---

### User Story 4 - Interactive Terminal Console Interface (Priority: P4)

As an emergency unit intake worker, I want an intuitive and resilient command-line menu interface, so that I can quickly perform intake, call patients, and monitor the queue without the application crashing on typing mistakes or invalid inputs.

**Why this priority**: Front-line intake staff require a robust, error-tolerant terminal interface that stays running during high-stress emergency unit shifts.

**Independent Test**: Can be tested by executing the interactive console loop, entering valid operations, intentionally submitting invalid menu choices or invalid triage levels, and verifying the interface recovers with helpful user guidance.

**Acceptance Scenarios**:

1. **Given** the main menu prompt, **When** the user selects the intake option, **Then** the system prompts for patient name and triage level, validates the inputs, and confirms addition to the queue.
2. **Given** an intake prompt for triage level, **When** the user inputs an invalid value (e.g., numbers outside 1-3, letters, or blank input), **Then** the system provides a clear validation message and prompts again without crashing.
3. **Given** the main menu prompt, **When** the user enters an unrecognized menu selection, **Then** the system informs the user of the invalid choice and re-displays the available options.
4. **Given** the main menu prompt, **When** the user selects the exit option, **Then** the system terminates gracefully with a clean exit message.

---

### Edge Cases

- **Queue Underflow**: Attempting to dequeue or peek when zero patients are waiting must return a graceful notification rather than terminating the process or throwing unhandled exceptions.
- **Priority Inversion Prevention**: A Level 1 patient arriving at any time while numerous Level 2 and Level 3 patients are queued must immediately be positioned at the head of the queue ahead of all Level 2 and Level 3 patients.
- **Timestamp Collisions / Close Arrivals**: Two or more patients assigned the same triage level arriving in close succession must preserve arrival sequence deterministically.
- **Boundary Validation**: Non-numeric or out-of-range triage levels (e.g., 0, 4, negative numbers, strings) must be rejected with helpful user feedback.
- **Empty / Whitespace Patient Names**: Blank or whitespace-only patient names must be detected and rejected during intake.
- **Queue State Integrity**: Inspecting the next patient (peek) or listing the full queue must never mutate or reorder the queue.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST record patient admissions with patient name, triage severity level (1 for Critical, 2 for Urgent, 3 for Standard), and arrival timestamp.
- **FR-002**: System MUST enforce deterministic triage hierarchy where Level 1 (Critical) patients are strictly prioritized over Level 2 (Urgent), and Level 2 patients are strictly prioritized over Level 3 (Standard).
- **FR-003**: System MUST preserve strict First-In, First-Out (FIFO) arrival order among patients possessing the identical triage severity level.
- **FR-004**: System MUST support an enqueue operation that positions any newly admitted patient at their exact priority-ordered position in the queue.
- **FR-005**: System MUST support a dequeue operation that removes and returns the next patient due for clinical attention according to priority and arrival rules.
- **FR-006**: System MUST support a peek operation that returns the next patient due for attention without removing them or mutating queue state.
- **FR-007**: System MUST handle dequeue and peek operations on an empty queue gracefully, delivering an informative response without causing application errors.
- **FR-008**: System MUST support a queue listing operation that returns all currently waiting patients in their exact service sequence.
- **FR-009**: System MUST support a statistics operation that calculates and returns active waiting counts categorized by each triage level (Level 1, Level 2, Level 3).
- **FR-010**: System MUST provide an interactive terminal interface offering menu choices to: add a patient, call the next patient, view current queue, view queue statistics, and exit.
- **FR-011**: System MUST validate all terminal inputs (e.g., non-empty names, valid integer triage levels 1 through 3, valid menu selections) and provide constructive feedback without terminating the session.

### Key Entities

- **Patient Record**: Represents an individual awaiting emergency medical attention. Key attributes include:
  - `name`: Non-empty text identifying the patient.
  - `triage_level`: Clinical priority indicator (1 = Critical, 2 = Urgent, 3 = Standard).
  - `arrived_at`: Timestamp recording the exact moment of patient admission.
- **Triage Queue**: The collection of waiting patient records maintained in deterministic priority and FIFO order.
- **Triage Statistics**: Summary metric containing patient counts broken down by triage level (Levels 1, 2, and 3) and total active queue count.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of patient retrieval operations (peek and dequeue) select the highest-priority, earliest-arrived patient across all valid test scenarios.
- **SC-002**: Critical (Level 1) patient insertions immediately take service precedence ahead of existing Level 2 and Level 3 patients 100% of the time.
- **SC-003**: Zero application crashes or unhandled exceptions occur during empty queue operations or invalid terminal input scenarios.
- **SC-004**: Users can complete a patient intake registration in under 15 seconds via the terminal menu.
- **SC-005**: Queue listing and triage breakdown statistics reflect the exact state of active patients with zero discrepancy after any combination of enqueues and dequeues.

## Assumptions

- **Single-Station In-Memory Operation**: The initial terminal application operates as a standalone in-memory tool for a single intake station; data persistence across application restarts is out of scope for v1.
- **Automatic Timestamping**: The arrival timestamp is recorded automatically at the moment of intake entry unless explicitly overridden for testing.
- **Deterministic Priority Tiers**: The emergency department strictly utilizes a 3-tier triage scale (1 = Critical, 2 = Urgent, 3 = Standard). Finer-grained sub-tiers or clinical re-triage score changes are out of scope for v1.
- **Standard Runtime Environment**: The software will run in a standard console/terminal environment using standard language runtime libraries without requiring external network connectivity or third-party package dependencies.
