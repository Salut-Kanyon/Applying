"""
Export in-memory transcripts from a running server debug endpoint or manually pasted data.
For a real submission, use this after each run to save transcripts and bug reports.
"""
import argparse
import json
from pathlib import Path
import requests
from app.scenarios import get_scenario
from app.llm import analyze_transcript

ROOT = Path(__file__).resolve().parents[1]
OUT_TRANSCRIPTS = ROOT / "outputs" / "transcripts"
OUT_REPORTS = ROOT / "outputs" / "bug_reports"


def save_call(base_url: str, call_sid: str):
    data = requests.get(f"{base_url}/debug/calls/{call_sid}", timeout=20).json()
    if "error" in data:
        raise RuntimeError(data["error"])

    scenario = get_scenario(data["scenario_id"])
    lines = [f"Scenario: {scenario.title}", f"Goal: {scenario.goal}", ""]
    for idx, turn in enumerate(data["turns"], start=1):
        lines.append(f"{idx:02d} {turn['speaker']}: {turn['text']}")
    transcript_text = "\n".join(lines)

    transcript_path = OUT_TRANSCRIPTS / f"{data['scenario_id']}_{call_sid}.txt"
    transcript_path.write_text(transcript_text, encoding="utf-8")
    print(f"Wrote {transcript_path}")

    report = analyze_transcript(scenario, transcript_text)
    report_path = OUT_REPORTS / f"{data['scenario_id']}_{call_sid}.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"Wrote {report_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True, help="Local or public server URL")
    parser.add_argument("--call-sids", nargs="+", required=True)
    args = parser.parse_args()

    OUT_TRANSCRIPTS.mkdir(parents=True, exist_ok=True)
    OUT_REPORTS.mkdir(parents=True, exist_ok=True)
    for sid in args.call_sids:
        save_call(args.base_url.rstrip("/"), sid)


if __name__ == "__main__":
    main()
