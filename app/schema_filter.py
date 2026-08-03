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
) -> list[ScoredTable]:
    question_vec = embed_text(question)
    tables_by_name = {t.name: t for t in tables}

    scored = []
    for table in tables:
        description = TABLE_DESCRIPTIONS.get(table.name, table.name)
        table_vec = embed_text(f"{table.name}: {description}")
        score = cosine_similarity(question_vec, table_vec)
        scored.append(ScoredTable(table=table, description=description, score=score))

    scored.sort(key=lambda s: s.score, reverse=True)
    relevant = [s for s in scored if s.score >= min_score][:top_k]

    if not relevant and scored:
        relevant = [scored[0]]

    # Transitive FK expansion: keep expanding until a full pass adds nothing
    # new. A single pass can miss tables reached through a table that was
    # ITSELF only added via expansion (e.g. order_items -> orders -> customers,
    # where 'orders' isn't in the original similarity-selected set).
    already_included = {s.table.name for s in relevant}
    changed = True
    while changed:
        changed = False
        for scored_table in list(relevant):  # safe: we only read, append happens below
            for fk in scored_table.table.foreign_keys:
                ref_name = fk.references_table
                if ref_name not in already_included and ref_name in tables_by_name:
                    relevant.append(
                        ScoredTable(
                            table=tables_by_name[ref_name],
                            description=TABLE_DESCRIPTIONS.get(ref_name, ref_name),
                            score=0.0,
                        )
                    )
                    already_included.add(ref_name)
                    changed = True

    return relevant