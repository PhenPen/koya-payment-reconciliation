
#!/usr/bin/env python3
"""Payment reconciliation."""

import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

latest_attempts = {}

with open("payments.jsonl", "r", encoding="utf-8") as file:
    for line in file:
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue

        if not isinstance(event, dict) or not event.get("txn_id"):
            continue

        try:
            timestamp = datetime.fromisoformat(
                event["ts"].replace("Z", "+00:00")
            )
        except (ValueError, TypeError, KeyError, AttributeError):
            continue

        txn_id = event["txn_id"]
        
        if (
            txn_id not in latest_attempts
            or timestamp >= latest_attempts[txn_id][0]
        ):
            latest_attempts[txn_id] = (timestamp, event)

successful = [
    event
    for _, event in latest_attempts.values()
    if event.get("status") == "success"
]

count = len(successful)

total = sum(
    (Decimal(str(event["amount"])) for event in successful),
    Decimal("0")
)

with open("expected.txt", "r", encoding="utf-8") as file:
    expected = int(file.read().strip())

if count != expected:
    print(
        f"Check failed: counted {count} successful payments, "
        f"expected {expected}."
    )
    print(
        "Something in the data isn't being handled "
        "the way the README describes."
    )
else:
    rounded_total = total.quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP
    )

    print(f"Check passed: {count} successful payments.")
    print(f"Your code: KOYA-{rounded_total}")
