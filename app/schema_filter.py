from dataclasses import dataclass

from embeddings import embed_text, cosine_similarity
from schema_metadata import TABLE_DESCRIPTIONS
from schema_introspection import TableInfo


@dataclass
class ScoredTable:
    table: TableInfo
    description: str
    score: float


def filter_relevant_tables(
    question: str,
    tables: list[TableInfo],
    top_k: int = 3,
    min_score: float = 0.2,
):
    question_vec = embed_text(question)

    scored = []

    for table in tables:
        description = TABLE_DESCRIPTIONS.get(table.name, table.name)

        table_vec = embed_text(
            f"{table.name}: {description}"
        )

        score = cosine_similarity(
            question_vec,
            table_vec
        )

        scored.append(
            ScoredTable(
                table=table,
                description=description,
                score=score
            )
        )

    scored.sort(
        key=lambda x: x.score,
        reverse=True
    )

    relevant = [
        s for s in scored
        if s.score >= min_score
    ][:top_k]

    if not relevant and scored:
        relevant = [scored[0]]

    return relevant