#!/usr/bin/env python3

import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def parse_amount(value):
    """Parse an amount that may be a number or a formatted string like "4,804.15"."""
    if isinstance(value, bool):
        raise InvalidOperation

    if isinstance(value, str):
        value = value.strip().replace(",", "").replace(" ", "")

    amount = Decimal(str(value))
    if not amount.is_finite():
        raise InvalidOperation

    return amount


def parse_timestamp(value):
    """Parse an ISO-8601 timestamp. Timestamps without an offset are UTC."""
    if not isinstance(value, str):
        raise ValueError("timestamp is not a string")

    timestamp = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    return timestamp


# Keep only the latest attempt for each transaction.
latest_attempts = {}

with open("payments.jsonl", "r", encoding="utf-8") as file:
    for line in file:
        line = line.strip()
        if not line:
            continue

        try:
            event = json.loads(line)
        except ValueError:
            continue

        if not isinstance(event, dict) or not event.get("txn_id"):
            continue

        try:
            timestamp = parse_timestamp(event["ts"])
        except (ValueError, TypeError):
            continue

        txn_id = event["txn_id"]

        if (
            txn_id not in latest_attempts
            or timestamp >= latest_attempts[txn_id][0]
        ):
            latest_attempts[txn_id] = (timestamp, event)

# Sum the latest attempts that were collected.
successful = 0
total = Decimal("0")
invalid_amounts = 0

for _, event in latest_attempts.values():
    if event.get("status") != "success":
        continue

    try:
        total += parse_amount(event["amount"])
        successful += 1
    except (InvalidOperation, ValueError, TypeError, KeyError):
        invalid_amounts += 1

# Read expected transaction count.
with open("expected.txt", "r", encoding="utf-8") as file:
    expected = int(file.read().strip())

# Verify reconciliation.
if invalid_amounts:
    print(f"Reconciliation failed: {invalid_amounts} successful transactions have invalid amounts.")

elif successful != expected:
    print(f"Check failed: counted {successful} successful payments, expected {expected}.")

else:
    rounded_total = total.quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP
    )

    print(f"Check passed: {successful} successful payments.")
    print(f"Your code: KOYA-{rounded_total}")
