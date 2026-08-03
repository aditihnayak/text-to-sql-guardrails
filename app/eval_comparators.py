import re

from multi_query_validator import compare_results
from query_executor import execute_readonly
from sqlalchemy.engine import Engine


def normalize_sql(sql: str) -> str:
    normalized = re.sub(r"\s+", " ", sql.strip().lower())
    normalized = normalized.rstrip(";")
    return normalized


def exact_match(generated_sql: str, golden_sql: str) -> bool:
    return normalize_sql(generated_sql) == normalize_sql(golden_sql)


def execution_match(engine: Engine, generated_sql: str, golden_sql: str) -> float:
    generated_result = execute_readonly(engine, generated_sql)
    golden_result = execute_readonly(engine, golden_sql)

    if generated_result.error or golden_result.error:
        return 0.0

    return compare_results(generated_result.rows, golden_result.rows)