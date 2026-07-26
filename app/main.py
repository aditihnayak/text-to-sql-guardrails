from fastapi import FastAPI
from pydantic import BaseModel

from db import engine
from schema_introspection import introspect_schema
from schema_filter import filter_relevant_tables
from prompt_constructor import build_prompt

app = FastAPI(title="Text-to-SQL Guardrails API")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/schema")
def get_schema():
    tables = introspect_schema(engine)
    return tables


class QuestionRequest(BaseModel):
    question: str


@app.post("/v1/debug/prompt")
def debug_prompt(req: QuestionRequest):
    tables = introspect_schema(engine)
    relevant = filter_relevant_tables(req.question, tables)
    prompt = build_prompt(req.question, relevant)

    return {
        "prompt": prompt,
        "selected_tables": [t.table.name for t in relevant]
    }