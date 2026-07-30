from collections import Counter

ALTERNATIVE_STRATEGY_SUFFIX = (
    "\n\nWrite an ALTERNATIVE SQL query that answers the same question using a "
    "genuinely different strategy than the most obvious approach — for example, "
    "a subquery instead of a JOIN, or a different aggregation path — while still "
    "returning the same logical result."
)


def build_alternative_prompt(original_prompt: str) -> str:
    return original_prompt + ALTERNATIVE_STRATEGY_SUFFIX


def _row_to_comparable_tuple(row: dict) -> tuple:
    # Ignore column NAMES (two independently-generated queries may alias
    # columns differently) and compare on VALUES only, rounding floats to
    # avoid spurious mismatches from floating-point precision.
    values = []
    for v in row.values():
        if isinstance(v, float):
            values.append(round(v, 2))
        else:
            values.append(v)
    return tuple(sorted(values, key=str))


def compare_results(rows_a: list[dict], rows_b: list[dict]) -> float:
    """Returns an agreement score in [0, 1] based on multiset overlap of
    row VALUES between two independently generated/executed query results."""
    if not rows_a and not rows_b:
        return 1.0
    if not rows_a or not rows_b:
        return 0.0

    multiset_a = Counter(_row_to_comparable_tuple(r) for r in rows_a)
    multiset_b = Counter(_row_to_comparable_tuple(r) for r in rows_b)

    intersection = sum((multiset_a & multiset_b).values())
    union = sum((multiset_a | multiset_b).values())

    return intersection / union if union else 1.0