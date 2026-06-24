# PGAI Final Submission Package

**This folder is the curated deliverable.** Old long filenames were moved to `archive/`.

## Quick open Phone +16292841876

```bash
cd ~/Desktop/pgai_voice_challenge
open submission/recordings
open submission/transcripts
open submission/bug_reports
open submission/docs/traceability.csv
```

## Folder layout

```
submission/
├── README.md                 ← you are here
├── recordings/               ← 10 mp3 files (clean names)
├── transcripts/              ← 10 txt files (clean names)
├── bug_reports/              ← 7 reviewer-ready reports
├── docs/
│   ├── architecture.md
│   ├── scenario_results.md
│   ├── bug_summary.md
│   └── traceability.csv
└── archive/                    ← old long names (do not submit)
```

## Old name → new name

| Old name (outputs/ or archive/) | New name (submission/) |
|----------------------------------|------------------------|
| `reschedule_cancel_confusion_CA2df4526….txt` | `transcripts/01_cancel_intent.txt` |
| `insurance_location_two_intents_CA53ad3c6….txt` | `transcripts/02_multi_intent.txt` |
| `fax_records_CA4b08d1df….txt` | `transcripts/03_fax_records.txt` |
| `weekend_closed_CAbb6d18c….txt` | `transcripts/04_identity_loop.txt` |
| `schedule_basic_CAec901cb….txt` (transfer bug) | `transcripts/05_handoff_failure.txt` |
| `schedule_basic_CAcf50ce6….txt` (duplicate appt) | `transcripts/06_duplicate_appt.txt` |
| `schedule_basic_CA3b16dcb….txt` (success) | `transcripts/07_partial_success.txt` |
| `wrong_dob_correction_CAec6d1fb….txt` | `transcripts/08_wrong_dob.txt` |
| `refill_missing_info_CAdec7a5e….txt` | `transcripts/09_refill_scenario.txt` |
| `symptoms_triage_boundary_CA00ecbb7….txt` | `transcripts/10_triage_boundary.txt` |

## Loom — top 3 files

| Bug | Recording | Transcript |
|-----|-----------|------------|
| Cancel intent | `recordings/01_cancel_intent.mp3` | `transcripts/01_cancel_intent.txt` |
| Multi-intent | `recordings/02_multi_intent.mp3` | `transcripts/02_multi_intent.txt` |
| Phantom phone | `recordings/03_fax_records.mp3` | `transcripts/03_fax_records.txt` |

## Note

`outputs/` still has the **original export names** from `export_results`. That folder was not renamed — only `submission/` was reorganized for the final package.
