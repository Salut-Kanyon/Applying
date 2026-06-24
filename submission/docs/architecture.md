# Architecture

This project uses a webhook-driven voice architecture. A Python script starts outbound calls through Twilio to the Pretty Good AI assessment number (`+1-805-439-8008`). For each call, Twilio requests TwiML from a FastAPI server running locally. The server speaks as a simulated patient, listens to the healthcare agent using Twilio speech recognition, stores each turn in memory, and uses OpenAI to generate the next patient response based on the assigned scenario.

## Key design choices

**Turn-based webhooks instead of real-time media streaming.** This is faster to ship, easier to debug, and sufficient for evaluating lucid voice conversations — Kevin's #1 criterion.

**Hybrid scripted + LLM patient routing.** Deterministic replies handle identity confirmation, yes/no, and repeat requests (low latency). OpenAI handles open-ended turns with a 1.2s timeout and bridge phrases to avoid awkward silence.

**Scenario-driven testing.** Each call loads a persona, goal, and edge case from `app/scenarios.py`. The patient bot actively steers toward the test outcome.

**Post-call analysis.** Transcripts export from the in-memory call store. Bug reports are generated with evidence, severity, and expected behavior.

## Stack

| Component | Role |
|-----------|------|
| `app/run_calls.py` | Initiates outbound Twilio calls |
| `app/server.py` | FastAPI webhooks for TwiML |
| `app/llm.py` | Patient response generation |
| `app/scripted.py` | Deterministic patient replies |
| `app/agent_intent.py` | PGAI intent detection for routing |
| Cloudflare Tunnel / ngrok | Exposes localhost to Twilio |
| Twilio Voice | Telephony + recording |
| OpenAI | Patient simulation + bug analysis |

## Run flow

```
run_calls → Twilio dials PGAI → PGAI speaks → Twilio STT → webhook → patient reply → TwiML → loop
                                                                                      ↓
                                                                              export_results → transcript + bug report
```

## Tunnel note

`PUBLIC_BASE_URL` in `.env` must match the current Cloudflare or ngrok HTTPS URL. Restart the server after updating it.
