# Multi-intent question ignored (insurance + location)

**Confidence:** High  
**Scenario:** `insurance_location_two_intents`  
**Call SID:** `CA53ad3c68c776ada4c9e5c2103a837c2f`  
**Recording:** `recordings/02_multi_intent.mp3`  
**Transcript:** `transcripts/02_multi_intent.txt`  
**Severity:** High

## Why it matters

New patients often ask insurance and location in one breath. Ignoring both forces unnecessary callbacks and blocks decision-making before booking.

## Evidence

| Line | Speaker | Quote |
|------|---------|-------|
| 01 | patient | "Hi, do you take Blue Cross insurance, and where exactly is your office?" |
| 05 | patient | "March fourth, 1990. Do you accept Blue Cross?" |
| 06 | pgai_agent | "I can't proceed further right now but I can make sure our Clinic support team follows up with you." |
| 08 | pgai_agent | "Connecting you to a representative… It's a pretty good. AI test line, goodbye." |

Neither insurance acceptance nor office address is answered at any point in the 68-second call.

## Expected behavior

The agent should answer both questions directly, or acknowledge both and answer them sequentially before ending the call.

## Actual behavior

The agent collects identity, declares it cannot proceed, transfers, and hangs up without addressing either question.

## Reproduction steps

1. Call the assessment line.
2. Ask: "Hi, do you take Blue Cross insurance, and where exactly is your office?"
3. Provide name and DOB when asked.

## Root cause hypothesis

Single-intent routing — the agent treats the call as identity verification only and does not retain or prioritize the opening multi-part question.

## Failure type

**Intent failure** · **Workflow failure**
