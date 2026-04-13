# Refactoring Notes

## Changes made

**1. Guard clauses replace nested `if`s**
The original used three levels of nesting. Inverting each condition and using `continue` flattens the logic so the happy path is obvious.

**2. Redundant check consolidated**
`if item.get('amount')` followed by `if item['amount'] > 0` was two checks for the same concern. Combining them into `if not amount or amount <= 0` (after extracting `amount`) removes the redundancy and avoids a double lookup.

**3. Dict literal instead of incremental construction**
Building `r` key-by-key across three lines was noisy. A single dict literal `{"id": ..., "amount": ...}` is more concise and idiomatic.

**4. Type hints added**
`list[dict[str, Any]]` (built-in generics, available since Python 3.9) makes the contract explicit without adding runtime overhead.

## Behaviour preserved
- Only items with `type == 'invoice'` and a positive `amount` are included.
- Missing or falsy `id` falls back to `"unknown"`.
