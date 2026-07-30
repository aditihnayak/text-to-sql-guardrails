from dataclasses import dataclass, field


@dataclass
class SanityCheckResult:
    passed: bool
    issues: list[str] = field(default_factory=list)


def check_result_sanity(rows: list[dict], expected_row_count_upper_bound: int | None = None) -> SanityCheckResult:
    issues = []

    if not rows:
        # Not necessarily wrong — zero rows can be a truthful answer — but
        # worth flagging for visibility rather than silently treating as fine.
        issues.append("Query returned zero rows — verify this is expected, not a bad filter.")
        return SanityCheckResult(passed=True, issues=issues)

    columns = list(rows[0].keys())

    for col in columns:
        values = [row[col] for row in rows]
        null_count = sum(1 for v in values if v is None)
        null_ratio = null_count / len(values)

        if null_ratio > 0.5:
            issues.append(
                f"Column '{col}' is {null_ratio:.0%} NULL — possible incorrect JOIN direction "
                f"(e.g. should be INNER JOIN instead of LEFT JOIN, or vice versa)."
            )

        numeric_values = [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
        if numeric_values and len(numeric_values) == len(values):
            if any(v < 0 for v in numeric_values) and _looks_like_count_or_amount(col):
                issues.append(f"Column '{col}' contains negative values, which is implausible for a count/amount field.")

    if expected_row_count_upper_bound is not None and len(rows) > expected_row_count_upper_bound:
        issues.append(
            f"Returned {len(rows)} rows, exceeding expected upper bound of {expected_row_count_upper_bound} — "
            f"possible JOIN fan-out duplicating rows."
        )

    return SanityCheckResult(passed=len(issues) == 0, issues=issues)


def _looks_like_count_or_amount(column_name: str) -> bool:
    lowered = column_name.lower()
    return any(kw in lowered for kw in ("count", "total", "sum", "amount", "price", "quantity"))