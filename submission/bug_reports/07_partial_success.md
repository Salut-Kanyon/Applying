# Partial success — appointment rescheduled (positive finding)

**Confidence:** N/A — this is a success, not a bug  
**Scenario:** `schedule_basic`  
**Call SID:** `CA3b16dcbd8dbfafc83200c397cca699a8`  
**Recording:** `recordings/07_partial_success.mp3`  
**Transcript:** `transcripts/07_partial_success.txt`

## Why it matters

Demonstrates balanced testing. PGAI can complete scheduling workflows when duplicate-appointment handling routes to reschedule instead of block.

## Evidence

| Line | Speaker | Quote |
|------|---------|-------|
| 11 | patient | "I'd like to go ahead and change that appointment, please." |
| 16 | pgai_agent | "you're scheduled for Monday, June, 22nd at 10:00 a.m." |
| 18 | pgai_agent | "I found an opening on Monday June 22nd at 11 a.m. with Kelly Noble" |
| 20 | pgai_agent | "Your appointment is now rescheduled for Monday June 22nd at 11:00 a.m. with Dr. Tell" |

## What worked

Patient pivoted from "book new" to "change existing." Agent pulled up the appointment, found a new slot, and confirmed the reschedule.

## Include in Loom

30 seconds — shows you are not only reporting failures.
