import json
import os
from abc import ABC, abstractmethod

from groq import Groq
from pydantic import BaseModel, Field


class SqlGenerationResult(BaseModel):
    sql: str = Field(description="The generated SQL query")
    explanation: str = Field(description="Plain-English explanation of what the query does")
    confidence: float = Field(ge=0.0, le=1.0, description="Model's self-reported confidence, 0 to 1")
    tables_used: list[str] = Field(description="Tables referenced in the query")


class LLMClient(ABC):
    @abstractmethod
    def generate_sql(self, prompt: str) -> SqlGenerationResult: ...


class GroqLLMClient(LLMClient):
    def __init__(self, model: str = "openai/gpt-oss-20b"):
        self.client = Groq(api_key=os.environ["GROQ_API_KEY"])
        self.model = model

    def generate_sql(self, prompt: str) -> SqlGenerationResult:
        schema = SqlGenerationResult.model_json_schema()

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "sql_generation_result",
                    "schema": schema,
                },
            },
        )

        raw = response.choices[0].message.content
        data = json.loads(raw)
        return SqlGenerationResult.model_validate(data)


def get_llm_client() -> LLMClient:
    return GroqLLMClient()