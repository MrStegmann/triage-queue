# Interface Contract: Interactive Terminal Console

**Contract Type**: CLI / Terminal User Interface  
**Entry Point**: `python -m triage_queue.cli` or `python src/triage_queue/cli/main.py`  
**Status**: Stable  

---

## 1. Main Menu Interface

Upon launching the application, the console displays a formatted header and menu loop:

```text
==================================================
   EMERGENCY UNIT TRIAGE QUEUE MANAGER
==================================================
1. Register New Patient (Intake)
2. Call Next Patient for Service (Dequeue)
3. Peek Next Patient in Line
4. View Current Triage Queue
5. View Triage Workload Statistics
6. Exit System
--------------------------------------------------
Select an option (1-6): 
```

### Options & Behaviors

| Option | Action | Input Requirements | Success Output | Empty / Error Behavior |
|---|---|---|---|---|
| `1` | Intake Patient | - Patient Name (non-empty)<br>- Triage Level (`1`, `2`, or `3`) | Confirmation with Patient ID, Name, Level, and Timestamp | Reprompts on invalid name or out-of-range triage level until valid or cancelled |
| `2` | Call Next Patient | None | Details of the dequeued patient called into clinical care | "Queue is empty. No patients currently waiting." |
| `3` | Peek Next Patient | None | Details of next patient without removing them | "Queue is empty. No patients currently waiting." |
| `4` | View Queue | None | Sequentially numbered table of all waiting patients in service order | "Queue is empty. No patients currently waiting." |
| `5` | View Statistics | None | Table/breakdown of counts for Critical, Urgent, Standard, and Total | Displays counts (0 if empty) without errors |
| `6` | Exit System | None | "Exiting Emergency Unit Triage Queue Manager. Goodbye." | Terminates process with exit code `0` |

---

## 2. Interactive Input Dialogs & Validation Loops

### 2.1 Patient Registration Flow

```text
--- Patient Intake ---
Enter Patient Name: [INPUT: e.g. John Doe]
Enter Triage Level (1=Critical, 2=Urgent, 3=Standard): [INPUT: e.g. 1]

[SUCCESS] Patient successfully admitted:
  ID:          PT-1001
  Name:        John Doe
  Severity:    Level 1 (Critical)
  Arrival:     2026-10-27 10:30:00
```

#### Validation & Recovery Rules:
1. **Empty / Whitespace Name**:
   ```text
   [ERROR] Patient name cannot be blank. Please enter a valid name.
   Enter Patient Name: 
   ```
2. **Invalid Triage Level (non-integer, out of range)**:
   ```text
   [ERROR] Invalid triage level 'abc'. Must be 1 (Critical), 2 (Urgent), or 3 (Standard).
   Enter Triage Level (1=Critical, 2=Urgent, 3=Standard): 
   ```

---

### 2.2 Calling the Next Patient (Dequeue)

#### Non-Empty Output:
```text
[DISPATCH] Calling next patient for care:
  ID:          PT-1001
  Name:        John Doe
  Severity:    Level 1 (Critical)
  Arrival:     2026-10-27 10:30:00
```

#### Empty Queue Output:
```text
[INFO] The triage queue is currently empty. No patients waiting.
```

---

### 2.3 Peeking the Next Patient

#### Non-Empty Output:
```text
[PEEK] Next patient in line (remains queued):
  ID:          PT-1002
  Name:        Jane Smith
  Severity:    Level 2 (Urgent)
  Arrival:     2026-10-27 10:32:15
```

#### Empty Queue Output:
```text
[INFO] The triage queue is currently empty. No patients waiting.
```

---

### 2.4 Queue Listing View

```text
================================================================================
#    ID        PRIORITY               NAME                  ARRIVAL TIME
================================================================================
1    PT-1001   Level 1 (Critical)     John Doe              2026-10-27 10:30:00
2    PT-1004   Level 1 (Critical)     Alice Brown           2026-10-27 10:35:10
3    PT-1002   Level 2 (Urgent)       Jane Smith            2026-10-27 10:32:15
4    PT-1003   Level 3 (Standard)     Bob Wilson            2026-10-27 10:33:00
================================================================================
Total patients waiting: 4
```

---

### 2.5 Queue Statistics View

```text
========================================
       TRIAGE WORKLOAD STATISTICS
========================================
  Level 1 (Critical):      2
  Level 2 (Urgent):        1
  Level 3 (Standard):      1
----------------------------------------
  Total Waiting:           4
========================================
```

---

### 2.6 Unrecognized Menu Selection

```text
Select an option (1-6): 9
[ERROR] Unrecognized selection '9'. Please enter a number between 1 and 6.
```

The application immediately displays the main prompt again without crashing or losing queue state.
