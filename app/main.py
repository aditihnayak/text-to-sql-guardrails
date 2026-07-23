from fastapi import FastAPI
from db import engine
from schema_introspection import introspect_schema

app = FastAPI(title="Text-to-SQL Guardrails API")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/schema")
def get_schema():
    tables = introspect_schema(engine)
    return tables