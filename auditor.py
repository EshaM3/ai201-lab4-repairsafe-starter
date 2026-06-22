import json
import os
import uuid
from datetime import datetime, timezone
from config import LOG_FILE


def log_interaction(question: str, tier: str, response: str, reason: str = "") -> None:
    """
    Append a structured record of this interaction to the audit log.

    TODO — Milestone 3:

    Before writing any code, complete specs/auditor-spec.md. The key decisions
    are what fields to log, how much of the question and response to include,
    and how to handle the logs/ directory not existing yet.

    Each record should be a JSON object written as a single line to LOG_FILE
    (defined in config.py as "logs/audit.jsonl").

    Required fields:
      - "timestamp"        : ISO 8601 datetime string
      - "tier"             : the safety tier assigned to this question
      - "question"         : the user's question (truncate to 300 chars if longer)
      - "response_preview" : first 200 characters of the response

    If the logs/ directory doesn't exist, create it before writing.

    Also print a one-line summary to the terminal so you can see logged
    interactions in real time without opening the file:
      e.g. [LOGGED] tier=caution | "How do I replace a faucet?" → 47 chars

    Design your log entry in specs/auditor-spec.md before implementing here.
    """
    interaction_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    entry = {
        "timestamp": timestamp,
        "interaction_id": interaction_id[:8],
        "tier": tier,
        "question": question[:300],
        "reason": reason,
        "response_preview": response[:200],
    }

    # Create logs/ on demand so the very first run on a fresh checkout doesn't
    # crash with FileNotFoundError (see specs/auditor-spec.md — Directory creation).
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    # One JSON object per line (.jsonl), appended so history is preserved.
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # One-line terminal summary for live monitoring; long fields are truncated
    # here only — the full values still live in the log file.
    print(
        f'[{timestamp}] id={interaction_id[:8]} tier={tier} '
        f'q="{question[:50]}" reason="{reason[:70]}" resp="{response[:50]}"'
    )
