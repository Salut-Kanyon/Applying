# Scenario Results

10 scenarios defined in `app/scenarios.py`. 9 tested with exported transcripts. 1 not completed.

| # | Scenario ID | Tested | Call SID | Recording | Result |
|---|-------------|--------|----------|-----------|--------|
| 1 | `schedule_basic` | Yes (×4 calls) | CAec901cb… / CAcf50ce6… / CA3b16dcb… | 05, 06, 07 | Handoff failure · Duplicate block · **Partial success** |
| 2 | `weekend_closed` | Yes | CAbb6d18cebd329b1ee9895f4557505974 | 04 | Identity loop — Sunday/hours never reached |
| 3 | `reschedule_cancel_confusion` | Yes | CA2df4526f407825aa63396c7630a07612 | 01 | **Cancel intent failure** |
| 4 | `refill_missing_info` | Yes | CAdec7a5edde26895eb56f2c511f57fc87 | 09 | Scenario covered; no isolated refill bug (identity loop + handoff dominate) |
| 5 | `insurance_location_two_intents` | Yes | CA53ad3c68c776ada4c9e5c2103a837c2f | 02 | **Multi-intent ignored** |
| 6 | `wrong_dob_correction` | Yes | CAec6d1fb2c67b0dea7683829e96d010b9 | 08 | DOB accepted; call ends at handoff failure |
| 7 | `symptoms_triage_boundary` | Yes | CA00ecbb766c6a41f7397513a2759ced92 | 10 | PGAI gives 911/urgent-care guidance; debatable quality gap |
| 8 | `interruptions` | Yes (archived) | CA79d70e29f0755ad644b877d3349929ea | archived | Handoff failure; weak evidence for "afternoon ignored" |
| 9 | `fax_records` | Yes | CA4b08d1df6155f4426bde7c7cebc292d6 | 03 | **Phantom phone + fax status** |
| 10 | `after_hours_urgent_refill` | **No** | — | — | Not exported — do not claim tested |

## Coverage summary

- **10 calls submitted** in `recordings/` (minimum requirement met)
- **9 of 10 scenarios** have evidence
- **6 featured PGAI bugs** + 1 positive finding for Loom
- **41 total recordings** in `Audio/` archive (not part of submission package)

## Calls excluded from submission

| Call SID | Reason |
|----------|--------|
| CAcebeab2… | 3-line invalid call |
| CA640d383… | Truncated / invalid |
| CA09d48eec… / CAb9a84e2… | 4-second failed connects |
| Extra schedule_basic duplicates | Same failure themes already represented |

## Patient bot notes

- Patient bot confirms identity when asked but may repeat primary request instead of saying "yes, that's correct" (see identity loop call).
- Patient bot incorrectly confirmed phantom phone number "6292841876" — weakens data-integrity attribution; noted in fax bug report.
