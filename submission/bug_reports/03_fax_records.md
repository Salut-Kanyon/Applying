# Fax call: phantom phone number + fax status never confirmed

**Confidence:** High (phantom phone) · Medium (fax status)  
**Scenario:** `fax_records`  
**Call SID:** `CA4b08d1df6155f4426bde7c7cebc292d6`  
**Recording:** `recordings/03_fax_records.mp3`  
**Transcript:** `transcripts/03_fax_records.txt`  
**Severity:** High

## Why it matters

Reading back a phone number the patient never provided is a data-integrity failure. Repeatedly failing to answer a yes/no fax question after four asks is a workflow failure that leaves the patient without actionable information.

---

## Issue A — Phantom phone number (High confidence)

### Evidence

| Line | Speaker | Quote |
|------|---------|-------|
| 05 | patient | "August 30, 1985. Did my fax arrive?" |
| 09 | patient | "Sarah Miller, August 30, 1985. Fax status?" |
| 10 | pgai_agent | "I have Sarah Miller date of birth August 30th 1985 and the phone number as 6292841876. Is that correct?" |

The patient never stated 6292841876 in lines 01–09.

### Expected behavior

Only read back information the patient provided, or ask for the phone number explicitly before confirming it.

### Actual behavior

The agent asserts a specific phone number and asks the patient to confirm it.

### Failure type

**Data integrity issue**

---

## Issue B — Fax status never confirmed (Medium confidence)

### Evidence

| Line | Speaker | Quote |
|------|---------|-------|
| 13 | patient | "Did the referral fax arrive? How send records?" |
| 17 | patient | "Did you check if the fax arrived?" |
| 19 | patient | "Did you verify if the fax arrived?" |
| 21 | patient | "Did the fax arrive or not?" |
| 22 | pgai_agent | "I can't confirm that directly right now, the clinic support team has the request…" |

### Expected behavior

Give a direct answer if known, or clearly state inability to check and provide a concrete next step (callback window, what was ticketed, alternative contact).

### Actual behavior

Four patient asks receive variations of "I sent it to the team" with no yes/no answer.

### Failure type

**Workflow failure**

## Reproduction steps

1. Call as a patient asking about referral fax status.
2. Provide name and DOB when asked.
3. Do not provide a phone number; observe whether the agent invents one.
4. Ask "Did the fax arrive?" repeatedly after identity verification.

## Root cause hypothesis

Record lookup may pre-fill phone data without disclosure; fax lookup capability may not exist but the agent does not set expectations early.
