# Bug Summary — Final Submission

## Featured bugs (Loom + primary report)

| Rank | Bug | Confidence | Severity | Recording | Report |
|------|-----|------------|----------|-----------|--------|
| 1 | Cancel intent → "Something's not right" | **High** | High | `01_cancel_intent.mp3` | `01_cancel_intent.md` |
| 2 | Multi-intent ignored (insurance + location) | **High** | High | `02_multi_intent.mp3` | `02_multi_intent.md` |
| 3 | Phantom phone number on file | **High** | High | `03_fax_records.mp3` | `03_fax_records.md` |
| 4 | Identity verification loop | **Medium-High** | High | `04_identity_loop.mp3` | `04_identity_loop.md` |
| 5 | Failed handoff → test-line goodbye | **High** | High | `05_handoff_failure.mp3` | `05_handoff_failure.md` |
| 6 | Duplicate appointment blocks booking | **Medium-High** | Medium | `06_duplicate_appt.mp3` | `06_duplicate_appt.md` |

## Positive finding

| Finding | Recording | Report |
|---------|-----------|--------|
| Appointment rescheduled successfully | `07_partial_success.mp3` | `07_partial_success.md` |

## Scenario coverage only (not featured in Loom)

| Call | Scenario | Notes |
|------|----------|-------|
| `08_wrong_dob.mp3` | wrong_dob_correction | DOB corrected and accepted; ends at handoff (merged into handoff bug class) |
| `09_refill_scenario.mp3` | refill_missing_info | Identity loop dominates; refill clarifiers never tested |
| `10_triage_boundary.mp3` | symptoms_triage_boundary | PGAI gives 911/urgent-care criteria; quality gap is debatable |

## Removed / merged

| Original | Action | Reason |
|----------|--------|--------|
| `08_phantom_phone` (duplicate mp3) | **Removed** | Identical audio to `03_fax_records`; wrong bug report content |
| `06_refill_no_clarifiers` as top bug | **Demoted** | Insufficient evidence — call never reached refill workflow |
| `07_triage_guidance_gap` as top bug | **Demoted** | PGAI did provide safety escalation; arguable not a bug |
| `09_constraint_update_ignored` | **Merged** into handoff failure | Call ends at goodbye; afternoon-not-ignored not proven |
| `05_fax_status` + `08_phantom` as separate ranks | **Merged** | Same call, one report with two issues |
| Handoff in insurance/refill/wrong_dob/interruptions | **Merged** | One bug class, `05_handoff_failure` is primary example |

## Failure type matrix

| Bug | Memory | Intent | Safety | Data integrity | Workflow |
|-----|--------|--------|--------|----------------|----------|
| Cancel intent | | ✓ | | | ✓ |
| Multi-intent | | ✓ | | | ✓ |
| Phantom phone | | | | ✓ | |
| Identity loop | ✓ | | | | ✓ |
| Handoff failure | | | | | ✓ |
| Duplicate appt | | | | | ✓ |
| Fax status (secondary) | | | | | ✓ |
| Triage (demoted) | | | ~ | | |

## Minimum Loom set

Play only: **01, 02, 03 (phantom phone clip), 07 (partial success)**. Mention 04, 05, 06 in traceability — do not play all audio.
