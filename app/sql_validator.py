import sqlparse
from sqlparse.sql import Parenthesis


class ValidationResult:
    def __init__(self, is_valid: bool, reason: str | None = None):
        self.is_valid = is_valid
        self.reason = reason

    def __repr__(self):
        return (
            f"ValidationResult(is_valid={self.is_valid}, "
            f"reason={self.reason!r})"
        )


def _max_paren_depth(token, depth: int = 0) -> int:
    max_depth = depth

    for child in getattr(token, "tokens", []):
        if isinstance(child, Parenthesis):
            max_depth = max(
                max_depth,
                _max_paren_depth(child, depth + 1),
            )
        else:
            max_depth = max(
                max_depth,
                _max_paren_depth(child, depth),
            )

    return max_depth


def _is_meaningful_statement(stmt) -> bool:
    """
    Returns True if the statement contains something other than
    whitespace or punctuation (like a stray ';').
    """
    return any(
        token.ttype not in (
            sqlparse.tokens.Whitespace,
            sqlparse.tokens.Punctuation,
        )
        for token in stmt.flatten()
    )


def validate_sql(
    sql: str,
    max_subquery_depth: int = 3,
) -> ValidationResult:
    try:
        statements = sqlparse.parse(sql)
    except Exception as e:
        return ValidationResult(
            is_valid=False,
            reason=f"SQL failed to parse: {e}",
        )

    if not statements:
        return ValidationResult(
            is_valid=False,
            reason="No SQL statement found",
        )

    # Ignore empty statements like ";" or " ; "
    non_empty_statements = [
        stmt
        for stmt in statements
        if _is_meaningful_statement(stmt)
    ]

    if not non_empty_statements:
        return ValidationResult(
            is_valid=False,
            reason="No SQL statement found",
        )

    if len(non_empty_statements) > 1:
        return ValidationResult(
            is_valid=False,
            reason=(
                f"Multiple SQL statements detected "
                f"({len(non_empty_statements)}); "
                "only a single SELECT is allowed"
            ),
        )

    stmt = non_empty_statements[0]

    if stmt.get_type() != "SELECT":
        return ValidationResult(
            is_valid=False,
            reason=(
                f"Only SELECT statements are permitted; "
                f"got '{stmt.get_type()}'"
            ),
        )

    depth = _max_paren_depth(stmt)

    if depth > max_subquery_depth:
        return ValidationResult(
            is_valid=False,
            reason=(
                f"Subquery nesting depth {depth} exceeds "
                f"max allowed {max_subquery_depth}"
            ),
        )

    return ValidationResult(is_valid=True)