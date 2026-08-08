import logging
import time
from dataclasses import dataclass, field

from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger("query_executor")


@dataclass
class ExecutionResult:
    rows: list[dict] = field(default_factory=list)
    row_count: int = 0
    execution_time_ms: float = 0.0
    error: str | None = None


def execute_readonly(engine: Engine, sql: str) -> ExecutionResult:
    start = time.perf_counter()

    try:
        with engine.connect() as conn:
            # execution_options(isolation_level=...) sets the transaction's
            # isolation level for THIS connection's transaction only — it does
            # not mutate global engine state, so concurrent requests using
            # other connections from the pool are unaffected.
            conn = conn.execution_options(isolation_level="SERIALIZABLE")

            trans = conn.begin()

            try:
                conn.execute(text("SET TRANSACTION READ ONLY"))
                result = conn.execute(text(sql))

                rows = [dict(row._mapping) for row in result.fetchall()]
                execution_time = (time.perf_counter() - start) * 1000

                logger.info(
                    "query_executed",
                    extra={
                        "event": "query_executed",
                        "row_count": len(rows),
                        "execution_time_ms": round(execution_time, 2),
                    },
                )

                return ExecutionResult(
                    rows=rows,
                    row_count=len(rows),
                    execution_time_ms=execution_time,
                )

            finally:
                # Always roll back — even a read-only SELECT gets rolled back
                # rather than committed. There's nothing to persist from a
                # read, and this guarantees zero write side effects no matter
                # what happened above.
                trans.rollback()

    except Exception as e:
        execution_time = (time.perf_counter() - start) * 1000

        logger.error(
            "query_execution_failed",
            extra={
                "event": "query_execution_failed",
                "error": str(e),
                "execution_time_ms": round(execution_time, 2),
            },
        )

        return ExecutionResult(
            error=str(e),
            execution_time_ms=execution_time,
        )