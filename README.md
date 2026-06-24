# Pretty Good AI Voice Bot Challenge

> **Final submission artifacts:** see [`submission/`](submission/) — recordings, transcripts, and bug reports with clean names.  
> The `outputs/` folder keeps original export filenames from `export_results`.

This repo contains a Python voice bot that calls the Pretty Good AI assessment line and acts as a realistic patient. It runs multiple healthcare call scenarios, records calls through Twilio, stores transcripts, and generates bug reports.

## What it does

- Calls only the assessment number: `+1-805-439-8008`
- Runs realistic patient scenarios: scheduling, refills, office hours, insurance, interruptions, safety boundaries, and edge cases
- Uses Twilio Voice for calls and recordings
- Uses FastAPI webhooks to manage conversation turns
- Uses OpenAI to generate realistic patient responses and analyze transcripts
- Exports transcripts and bug reports for submission

## Setup

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Fill in:

- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_PHONE_NUMBER`
- `OPENAI_API_KEY`
- `PUBLIC_BASE_URL`

Keep:

```bash
TARGET_PHONE_NUMBER=+18054398008
```

The code contains a safety check that blocks calls to any other target number.

### 3. Run the webhook server

```bash
uvicorn app.server:app --reload --port 8000
```

### 4. Expose the local server

**Cloudflare (recommended):**
```bash
cloudflared tunnel --url http://localhost:8000
```

**Or ngrok:**
```bash
ngrok http 8000
```

Copy the HTTPS URL into `.env` as `PUBLIC_BASE_URL` (no trailing slash). Restart uvicorn after updating.

### 5. Run 10 calls

```bash
python -m app.run_calls --limit 10 --delay 20
```

## Export transcripts and bug reports

After each call, copy the call SIDs printed in the terminal. Then run:

```bash
python -m app.export_results --base-url http://localhost:8000 --call-sids CALL_SID_1 CALL_SID_2
```

Outputs are saved in:

- `outputs/transcripts/`
- `outputs/bug_reports/`

## Submission package

Curated deliverables are in `submission/`:

```
submission/
├── recordings/          # 10 call recordings (.mp3)
├── transcripts/         # Matching transcripts
├── bug_reports/         # Reviewer-ready bug write-ups
└── docs/
    ├── architecture.md
    ├── scenario_results.md
    ├── bug_summary.md
    └── traceability.csv
```

See `submission/docs/bug_summary.md` for the final ranked bug list and Loom recommendations. For file naming, traceability, and Loom walkthrough pointers, see [`submission/README.md`](submission/README.md).

## Scenarios

The bot includes 10 scenarios:

1. Basic appointment scheduling
2. Weekend appointment trap
3. Reschedule then cancel confusion
4. Medication refill with missing dosage
5. Insurance and location in one question
6. Wrong DOB then correction
7. Medical advice safety boundary
8. Interruptions and changing constraints
9. Fax and records request
10. Urgent refill after hours

## Notes

Voice interaction quality matters most. The goal is not perfect code. The goal is realistic conversations, useful bugs, clear thinking, and evidence of iteration.
