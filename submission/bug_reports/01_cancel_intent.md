# Cancel intent rejected with "Something's not right"

**Confidence:** High  
**Scenario:** `reschedule_cancel_confusion`  
**Call SID:** `CA2df4526f407825aa63396c7630a07612`  
**Recording:** `recordings/01_cancel_intent.mp3`  
**Transcript:** `transcripts/01_cancel_intent.txt`  
**Severity:** High

## Why it matters

When a patient pivots from reschedule to cancel, the agent must recognize and act on the final intent. A generic error with no resolution path blocks a basic workflow and erodes trust.

## Evidence

| Line | Speaker | Quote |
|------|---------|-------|
| 09 | patient | "Just cancel my appointment, please." |
| 10 | pgai_agent | "Something's not right." |
| 11 | patient | "I said cancel, not reschedule." |
| 12 | pgai_agent | "Something's not right." |
| 13 | patient | "I don't want to keep the appointment." |
| 16 | pgai_agent | "Connecting you to a representative… Hello. A pretty good. Line." |

## Expected behavior

After the patient says "Just cancel my appointment," the agent should confirm cancellation intent and either complete the cancel or explain the next step clearly.

## Actual behavior

The agent responds with a non-actionable error twice, then transfers to a test-line message without confirming cancellation.

## Reproduction steps

1. Call +1-805-439-8008 as a patient with an existing appointment.
2. Open with: "Hi, I need to reschedule my appointment, actually maybe cancel it."
3. Complete identity verification.
4. Say clearly: "Just cancel my appointment, please."

## Root cause hypothesis

Intent-state machine does not update when the patient overrides an earlier reschedule request. The agent falls back to a generic failure phrase instead of re-parsing the latest intent.

## Failure type

**Intent failure** · **Workflow failure**
