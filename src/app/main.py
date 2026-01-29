"""CLI entrypoint for TicketAI (stubbed)."""

import argparse
import json
import sys
from pathlib import Path

# Ensure "src" is on sys.path when running as a script
SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from app.config import get_settings
from app.logging_setup import setup_logging, create_request_id


def load_ticket(file_path: str) -> str:
    return Path(file_path).read_text(encoding="utf-8")


def stub_pipeline(ticket_text: str) -> dict:
    return {
        "summary": "Stubbed summary: provide short summary here.",
        "category": "General",
        "priority": "Medium",
        "queue": "Support L1",
        "confidence": 0.0,
        "needs_human_review": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="TicketAI minimal skeleton")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Ticket text")
    group.add_argument("--file", type=str, help="Path to ticket file")
    parser.add_argument("--output", choices=["json", "pretty"], default="json")
    args = parser.parse_args()

    settings = get_settings()
    logger = setup_logging(settings.log_level)
    request_id = create_request_id()

    ticket_text = load_ticket(args.file) if args.file else args.text
    if len(ticket_text) > settings.max_input_length:
        ticket_text = ticket_text[: settings.max_input_length]
        logger.warning("ticket_truncated", extra={"request_id": request_id})

    logger.info("triage_start", extra={"request_id": request_id, "input_length": len(ticket_text)})

    result = stub_pipeline(ticket_text)
    payload = {
        "request_id": request_id,
        **result,
        "metadata": {"input_length": len(ticket_text), "stub": True},
    }

    if args.output == "pretty":
        print(json.dumps(payload, indent=2))
    else:
        print(json.dumps(payload))


if __name__ == "__main__":
    main()
