import logging

from fastapi import FastAPI
from pydantic import BaseModel

from db import engine
from schema_introspection import introspect_schema
from schema_filter import filter_relevant_tables
from prompt_constructor import build_prompt
from llm_client import get_llm_client
from guardrail import apply_guardrails
from query_executor import execute_readonly

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

app = FastAPI(title="Text-to-SQL Guardrails API")

llm_client = get_llm_client()


class QuestionRequest(BaseModel):
    question: str


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/schema")
def get_schema():
    return introspect_schema(engine)


@app.post("/v1/debug/prompt")
def debug_prompt(req: QuestionRequest):
    tables = introspect_schema(engine)
    relevant_tables = filter_relevant_tables(req.question, tables)
    prompt = build_prompt(req.question, relevant_tables)

    return {
        "prompt": prompt,
        "selected_tables": [t.table.name for t in relevant_tables],
    }


@app.post("/v1/query")
def run_query(req: QuestionRequest):
    # Step 1: Get database schema
    tables = introspect_schema(engine)

    # Step 2: Retrieve only relevant tables
    relevant_tables = filter_relevant_tables(req.question, tables)

    # Step 3: Build prompt for the LLM
    prompt = build_prompt(req.question, relevant_tables)

    # Step 4: Generate SQL using the LLM
    generation = llm_client.generate_sql(prompt)

    logger.info(
        "Generated SQL | Question=%s | SQL=%s | Confidence=%s",
        req.question,
        generation.sql,
        generation.confidence,
    )

    # Step 5: Validate SQL and apply guardrails
    guardrail_result = apply_guardrails(generation.sql)

    if not guardrail_result.allowed:
        return {
            "question": req.question,
            "generated_sql": generation.sql,
            "executed": False,
            "blocked_reason": guardrail_result.reason,
        }

    # Step 6: Execute SQL inside a read-only transaction
    execution = execute_readonly(engine, guardrail_result.sql)

    # Step 7: Return results
    return {
        "question": req.question,
        "generated_sql": guardrail_result.sql,
        "explanation": generation.explanation,
        "confidence": generation.confidence,
        "tables_used": generation.tables_used,
        "executed": execution.error is None,
        "rows": execution.rows,
        "row_count": execution.row_count,
        "execution_time_ms": execution.execution_time_ms,
        "error": execution.error,
    }