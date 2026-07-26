from few_shot_examples import FEW_SHOT_EXAMPLES
from schema_filter import ScoredTable


def format_schema_section(scored_tables: list[ScoredTable]) -> str:
    lines = []
    for st in scored_tables:
        table = st.table
        col_lines = ", ".join(
            f"{c.name} ({c.type}{', PK' if c.is_primary_key else ''})"
            for c in table.columns
        )
        lines.append(f"- {table.name}: {st.description}\n  columns: {col_lines}")

        for fk in table.foreign_keys:
            lines.append(
                f"  relationship: {table.name}.{fk.column} -> "
                f"{fk.references_table}.{fk.references_column}"
            )
    return "\n".join(lines)


def format_few_shot_section() -> str:
    blocks = []
    for ex in FEW_SHOT_EXAMPLES:
        blocks.append(f"Q: {ex['question']}\nSQL: {ex['sql']}")
    return "\n\n".join(blocks)


def build_prompt(question: str, scored_tables: list[ScoredTable]) -> str:
    schema_section = format_schema_section(scored_tables)
    few_shot_section = format_few_shot_section()

    return f"""You are a SQL expert. Given a database schema and a question, write a single PostgreSQL query that answers the question.

Rules:
- Only use tables and columns listed in the schema below. Never invent a table or column name.
- If the question cannot be answered with this schema, say so instead of guessing.
- Return only the SQL query, no explanation.

Schema:
{schema_section}

Examples:
{few_shot_section}

Question: {question}
SQL:"""