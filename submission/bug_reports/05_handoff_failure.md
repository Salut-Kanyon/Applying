# Failed handoff ends at test-line goodbye

**Confidence:** High  
**Scenario:** `schedule_basic`  
**Call SID:** `CAec901cb53ebe904b240201ec601a9f6c`  
**Recording:** `recordings/05_handoff_failure.mp3`  
**Transcript:** `transcripts/05_handoff_failure.txt`  
**Severity:** High

## Why it matters

This failure mode appeared in multiple calls (insurance, refill, wrong DOB, interruptions). When PGAI transfers mid-workflow, the patient hears a test-line goodbye and the task is abandoned. This is the clearest example because scheduling was actively in progress.

## Evidence

| Line | Speaker | Quote |
|------|---------|-------|
| 12 | pgai_agent | "Let me check for openings next week." |
| 16 | pgai_agent | "I'm checking that for you. Connecting you to a representative, please. Wait." |
| 18 | pgai_agent | "You've reached the pretty good. AI test line, goodbye." |
| 19 | patient | "Hello? I think we got disconnected. I just want to schedule my appointment." |
| 20 | pgai_agent | "[No input detected]" |

## Expected behavior

Complete the scheduling check or transfer to a live agent who continues the workflow. Do not drop the call to a test-line recording.

## Actual behavior

Mid-scheduling transfer terminates at an automated goodbye. Patient attempts to re-engage; agent does not recover context.

## Reproduction steps

1. Call to schedule a routine check-up next week.
2. Complete identity verification as Maria.
3. Confirm visit type as routine check-up.
4. Wait while agent checks openings.

## Root cause hypothesis

Transfer target is misconfigured or routes to a test IVR instead of a continuation path. No session recovery after disconnect.

## Related calls (same root cause — not separate top bugs)

| Call SID | Scenario | Transcript |
|----------|----------|------------|
| CA53ad3c68c776ada4c9e5c2103a837c2f | insurance_location | `02_multi_intent.txt` line 08 |
| CAdec7a5edde26895eb56f2c511f57fc87 | refill_missing_info | `09_refill_scenario.txt` line 18 |
| CA79d70e29f0755ad644b877d3349929ea | interruptions | archived — same goodbye pattern |
| CAec6d1fb2c67b0dea7683829e96d010b9 | wrong_dob_correction | `08_wrong_dob.txt` line 12 |

## Failure type

**Workflow failure**
