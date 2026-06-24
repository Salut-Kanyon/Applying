# Duplicate-appointment rule blocks new booking without resolution

**Confidence:** Medium-High  
**Scenario:** `schedule_basic`  
**Call SID:** `CAcf50ce6d9d39c690e7e9bdaf8851af85`  
**Recording:** `recordings/06_duplicate_appt.mp3`  
**Transcript:** `transcripts/06_duplicate_appt.txt`  
**Severity:** Medium

## Why it matters

When a duplicate appointment exists, the agent should help the patient understand what's on file and offer reschedule/cancel — not dead-end the request.

## Evidence

| Line | Speaker | Quote |
|------|---------|-------|
| 17 | pgai_agent | "It looks like you already have an appointment of this same type on file. I can't book another 1 right now." |
| 21 | pgai_agent | "You have an office visit on Monday June 22nd at 11:00 a.m. with Dr. Kelly Noble." |
| 22 | patient | "I actually meant to schedule for next week, not confirm that one. Can we look for an appointment for next week instead?" |
| 23 | pgai_agent | "I can't book a new 1 right now because there is already a same type of appointment on file." |

The agent eventually reads the existing appointment (line 21) but still refuses to reschedule or find a new slot.

## Expected behavior

Offer to reschedule the existing appointment or clarify whether the on-file appointment satisfies the patient's need.

## Actual behavior

Hard block with repeated "can't book" message even after the patient clarifies intent.

## Reproduction steps

1. Call to schedule a routine check-up for next week as Maria (DOB March 14, 1988).
2. Proceed through identity verification.
3. Request earliest available appointment when duplicate is detected.

## Root cause hypothesis

Duplicate-detection logic is binary (block) without a reschedule branch in the conversation flow.

## Failure type

**Workflow failure**
