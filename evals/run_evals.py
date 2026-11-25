import json
import sys
from pathlib import Path

from ticket_handle.classifier import ClassificationError, TicketClassifier
from ticket_handle.config import build_llm, get_settings
from ticket_handle.models import Ticket, Urgency

GOLDEN_PATH = Path(__file__).parent / "golden.jsonl"
MIN_ACCURACY = 0.9


def load_cases() -> list[dict]:
    with GOLDEN_PATH.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> None:
    settings = get_settings()
    print(f"Model: {settings.model}")

    classifier = TicketClassifier(build_llm(settings))
    cases = load_cases()

    correct = 0
    safety_misses = []
    mistakes = []

    for case in cases:
        ticket = Ticket(ticket_id=case["id"], text=case["text"])
        try:
            result = classifier.classify(ticket)
        except ClassificationError as exc:
            mistakes.append(
                f"{case['id']} expected {case['expected_category']}, got ERROR ({exc.__cause__})"
            )
            continue

        if result.category == case["expected_category"]:
            correct += 1
        else:
            mistakes.append(
                f"{case['id']} expected {case['expected_category']}, got {result.category}"
            )

        if case["expected_urgency"] == Urgency.HIGH and result.urgency != Urgency.HIGH:
            safety_misses.append(case["id"])

    accuracy = correct / len(cases)
    print(f"Category accuracy: {correct}/{len(cases)} ({accuracy:.0%})")
    print(f"Safety misses: {len(safety_misses)} {safety_misses}")

    for mistake in mistakes:
        print(f" - {mistake}")

    passed = accuracy >= MIN_ACCURACY and not safety_misses
    print("PASS" if passed else "FAIL")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
