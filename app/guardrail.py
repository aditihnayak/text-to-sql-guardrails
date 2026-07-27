import logging

import sqlparse
from sql_validator import ValidationResult, validate_sql

logger = logging.getLogger("guardrail")


class GuardrailResult:
    def __init__(self, allowed: bool, sql: str, reason: str | None = None):
        self.allowed = allowed
        self.sql = sql  # possibly rewritten (e.g., LIMIT injected)
        self.reason = reason


def _has_limit_clause(sql: str) -> bool:
    return "limit" in sql.lower()


def _inject_row_limit(sql: str, max_rows: int) -> str:
    stripped = sql.rstrip().rstrip(";")
    return f"{stripped} LIMIT {max_rows};"


def apply_guardrails(sql: str, max_rows: int = 1000, max_subquery_depth: int = 3) -> GuardrailResult:
    validation: ValidationResult = validate_sql(sql, max_subquery_depth=max_subquery_depth)

    if not validation.is_valid:
        logger.warning("Blocked query. reason=%s sql=%s", validation.reason, sql)
        return GuardrailResult(allowed=False, sql=sql, reason=validation.reason)

    final_sql = sql
    if not _has_limit_clause(sql):
        final_sql = _inject_row_limit(sql, max_rows)
        logger.info("Injected row limit. original_sql=%s final_sql=%s", sql, final_sql)

    logger.info("Query allowed. sql=%s", final_sql)
    return GuardrailResult(allowed=True, sql=final_sql)