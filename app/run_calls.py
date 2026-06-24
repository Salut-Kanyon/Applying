import argparse
import time
from twilio.rest import Client
from app import config
from app.scenarios import SCENARIOS


def validate_config():
    missing = []
    for key, value in {
        "TWILIO_ACCOUNT_SID": config.TWILIO_ACCOUNT_SID,
        "TWILIO_AUTH_TOKEN": config.TWILIO_AUTH_TOKEN,
        "TWILIO_PHONE_NUMBER": config.TWILIO_PHONE_NUMBER,
        "PUBLIC_BASE_URL": config.PUBLIC_BASE_URL,
    }.items():
        if not value:
            missing.append(key)
    if missing:
        raise RuntimeError(f"Missing env vars: {', '.join(missing)}")
    if config.TARGET_PHONE_NUMBER != config.ALLOWED_TARGET:
        raise RuntimeError(f"Safety stop: TARGET_PHONE_NUMBER must be {config.ALLOWED_TARGET}")


def start_call(client: Client, scenario_id: str):
    url = f"{config.PUBLIC_BASE_URL}/voice/start/{scenario_id}"
    status_callback = f"{config.PUBLIC_BASE_URL}/voice/status"
    recording_callback = f"{config.PUBLIC_BASE_URL}/voice/recording"
    call = client.calls.create(
        to=config.TARGET_PHONE_NUMBER,
        from_=config.TWILIO_PHONE_NUMBER,
        url=url,
        method="POST",
        record=True,
        recording_status_callback=recording_callback,
        status_callback=status_callback,
        status_callback_event=["initiated", "ringing", "answered", "completed"],
    )
    return call.sid


def main():
    parser = argparse.ArgumentParser(description="Run Pretty Good AI voice challenge calls")
    parser.add_argument("--limit", type=int, default=10, help="Number of calls to run")
    parser.add_argument("--delay", type=int, default=15, help="Seconds between calls")
    args = parser.parse_args()

    validate_config()
    client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
    selected = SCENARIOS[: args.limit]

    print(f"Starting {len(selected)} calls to {config.TARGET_PHONE_NUMBER}")
    for scenario in selected:
        sid = start_call(client, scenario.id)
        print(f"Started {scenario.id}: {sid}")
        time.sleep(args.delay)


if __name__ == "__main__":
    main()
