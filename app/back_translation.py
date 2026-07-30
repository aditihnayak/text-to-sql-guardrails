from embeddings import cosine_similarity, embed_text
from llm_client import LLMClient

BACK_TRANSLATION_PROMPT_TEMPLATE = """You are a SQL expert. Given a SQL query, write the single natural-language question it answers.
Be specific and literal — describe exactly what the query computes, not a general summary of the tables involved.

SQL:
{sql}

Question:"""


def back_translate(sql: str, llm_client: LLMClient) -> str:
    prompt = BACK_TRANSLATION_PROMPT_TEMPLATE.format(sql=sql)
    result = llm_client.back_translate_sql(prompt)
    return result.question


def score_alignment(original_question: str, back_translated_question: str) -> float:
    original_vec = embed_text(original_question)
    back_vec = embed_text(back_translated_question)
    return cosine_similarity(original_vec, back_vec)