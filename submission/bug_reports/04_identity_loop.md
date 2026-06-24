# Identity verification loop blocks primary request

**Confidence:** Medium-High  
**Scenario:** `weekend_closed`  
**Call SID:** `CAbb6d18cebd329b1ee9895f4557505974`  
**Recording:** `recordings/04_identity_loop.mp3`  
**Transcript:** `transcripts/04_identity_loop.txt`  
**Severity:** High

## Why it matters

The patient cannot reach scheduling (including the Sunday/office-hours test) because the agent loops on identity confirmation. This is a core workflow blocker regardless of the specific appointment date requested.

> **Note:** This call does NOT demonstrate the PDF example bug (scheduling Sunday despite closed hours). The call never progresses past verification. Do not claim weekend-hours failure without a separate call showing it.

## Evidence

| Line | Speaker | Quote |
|------|---------|-------|
| 07 | patient | "July 8, 1975. Can I get Sunday?" |
| 08 | pgai_agent | "Please confirm your full name as David Kim and your date of birth as July 8th 1975…" |
| 12–18 | pgai_agent | Repeats same confirmation prompt four more times |
| 13–19 | patient | "I need Sunday at 10 AM, please." (×4) |
| 20 | pgai_agent | "I need your full name and date of birth 1 more time." |

Patient provided name (line 05) and DOB (line 07). Patient did not say "yes, that's correct" — but the agent already had both fields and still did not advance.

## Expected behavior

After receiving name and DOB, either accept confirmation once or proceed to address the scheduling request.

## Actual behavior

Six consecutive turns repeat identity confirmation without addressing Sunday scheduling or office hours.

## Reproduction steps

1. Request a Sunday appointment.
2. Provide name and DOB when asked.
3. Repeat the scheduling request instead of saying "yes, that's correct."

## Root cause hypothesis

Confirmation gate requires explicit "yes" but does not degrade gracefully when the patient restates their request. State machine stuck in `awaiting_confirmation`.

## Patient bot attribution

Patient bot deliberately avoids saying "yes, that's correct" and repeats the scheduling ask — this may prolong the loop. PGAI still owns the failure to break out or address the primary intent.

## Failure type

**Memory failure** · **Workflow failure**
