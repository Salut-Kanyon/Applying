from typing import Optional
import time

from fastapi import FastAPI, Form, Request
from fastapi.responses import Response, PlainTextResponse
from twilio.twiml.voice_response import VoiceResponse, Gather
from app.scenarios import get_scenario
from app.state import CALLS, CallState, Turn
from app.llm import patient_reply, sanitize_spoken_text
from app.profiling import RECENT_REPORTS, clear_profiler, start_profiler
from app import config

app = FastAPI(title="PGAI Voice Challenge Bot")

VOICE = "Polly.Joanna"
LANGUAGE = "en-US"


def twiml_response(vr: VoiceResponse) -> Response:
    return Response(content=str(vr), media_type="application/xml")


def add_gather(vr: VoiceResponse, call_sid: str, *, pause: int = 0, timeout: int = 6):
    gather = Gather(
        input="speech",
        action=f"/voice/respond?call_sid={call_sid}",
        method="POST",
        speech_timeout="auto",
        timeout=timeout,
        language=LANGUAGE,
        enhanced=True,
    )
    if pause:
        gather.pause(length=pause)
    vr.append(gather)
    vr.redirect(f"/voice/no-input?call_sid={call_sid}", method="POST")


def say_patient(vr: VoiceResponse, text: str):
    vr.say(sanitize_spoken_text(text), voice=VOICE, language=LANGUAGE)


def should_hangup(reply: str) -> bool:
    lower = reply.lower()
    return any(phrase in lower for phrase in ["goodbye", "bye", "thank you, that helps"])


def listen_for_agent(vr: VoiceResponse, call_sid: str):
    add_gather(vr, call_sid, pause=0, timeout=20)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/voice/start/{scenario_id}")
async def voice_start(scenario_id: str, CallSid: str = Form(...)):
    get_scenario(scenario_id)
    CALLS[CallSid] = CallState(call_sid=CallSid, scenario_id=scenario_id)

    vr = VoiceResponse()
    listen_for_agent(vr, CallSid)
    return twiml_response(vr)


@app.post("/voice/respond")
async def voice_respond(call_sid: str, SpeechResult: str = Form(default="")):
    wall_start = time.perf_counter()
    profiler = start_profiler(call_sid, SpeechResult.strip())
    try:
        with profiler.span("state_lookup"):
            state = CALLS.get(call_sid)
        if not state:
            vr = VoiceResponse()
            say_patient(vr, "Sorry, I lost my place. Goodbye.")
            vr.hangup()
            profiler.set_path("error_no_state")
            return twiml_response(vr)

        agent_text = SpeechResult.strip()
        if not agent_text:
            vr = VoiceResponse()
            listen_for_agent(vr, call_sid)
            profiler.set_path("empty_speech")
            return twiml_response(vr)

        with profiler.span("state_update"):
            state.turns.append(Turn("pgai_agent", agent_text))

        with profiler.span("scenario_fetch"):
            scenario = get_scenario(state.scenario_id)

        if state.turn_count >= config.MAX_TURNS_PER_CALL:
            reply = "Thank you, that helps. Goodbye."
            state.turns.append(Turn("patient_bot", reply))
            state.completed = True
            vr = VoiceResponse()
            say_patient(vr, reply)
            vr.hangup()
            profiler.set_path("scripted_max_turns")
            return twiml_response(vr)

        with profiler.span("patient_reply"):
            reply = patient_reply(scenario, state, agent_text)
        if not reply:
            vr = VoiceResponse()
            listen_for_agent(vr, call_sid)
            return twiml_response(vr)

        with profiler.span("state_update_post_reply"):
            state.turns.append(Turn("patient_bot", reply))
            state.turn_count += 1

        with profiler.span("twiml_generation"):
            vr = VoiceResponse()
            say_patient(vr, reply)

            if should_hangup(reply):
                state.completed = True
                vr.hangup()
            else:
                add_gather(vr, call_sid)
        return twiml_response(vr)
    finally:
        profiler.spans["total_request"] = (time.perf_counter() - wall_start) * 1000
        profiler.log_route()
        profiler.log()
        clear_profiler()


@app.post("/voice/no-input")
async def no_input(call_sid: str):
    state = CALLS.get(call_sid)
    vr = VoiceResponse()
    if state:
        listen_for_agent(vr, call_sid)
    else:
        say_patient(vr, "Sorry, I did not hear anything. Goodbye.")
        vr.hangup()
    return twiml_response(vr)


@app.post("/voice/status")
async def call_status(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    status = form.get("CallStatus", "unknown")
    print(f"Call {call_sid} status: {status}")
    return PlainTextResponse("ok")


@app.post("/voice/recording")
async def recording_status(request: Request):
    form = await request.form()
    print("Recording callback:", dict(form))
    return PlainTextResponse("ok")


@app.get("/debug/calls/{call_sid}")
def debug_call(call_sid: str):
    state = CALLS.get(call_sid)
    if not state:
        return {"error": "not found"}
    return {
        "call_sid": state.call_sid,
        "scenario_id": state.scenario_id,
        "turns": [t.__dict__ for t in state.turns],
        "completed": state.completed,
        "answered_name": state.answered_name,
        "answered_dob": state.answered_dob,
        "identity_verified": state.identity_verified,
        "goal_introduced": state.goal_introduced,
    }


@app.get("/debug/profiling")
def debug_profiling(limit: int = 20):
    return {"reports": RECENT_REPORTS[-limit:]}
