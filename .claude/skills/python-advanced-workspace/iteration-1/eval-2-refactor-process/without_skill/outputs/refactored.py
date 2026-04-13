from typing import Any


def process(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for item in data:
        if item.get("type") != "invoice":
            continue
        amount = item.get("amount")
        if not amount or amount <= 0:
            continue
        result.append({
            "id": item.get("id") or "unknown",
            "amount": amount,
        })
    return result
