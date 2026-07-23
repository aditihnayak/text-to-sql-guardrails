from dataclasses import dataclass, field
from sqlalchemy import inspect
from sqlalchemy.engine import Engine


@dataclass
class ColumnInfo:
    name: str
    type: str
    nullable: bool
    is_primary_key: bool


@dataclass
class ForeignKeyInfo:
    column: str
    references_table: str
    references_column: str


@dataclass
class TableInfo:
    name: str
    columns: list[ColumnInfo] = field(default_factory=list)
    foreign_keys: list[ForeignKeyInfo] = field(default_factory=list)


def introspect_schema(engine: Engine) -> list[TableInfo]:
    inspector = inspect(engine)
    tables = []

    for table_name in inspector.get_table_names():
        pk_constraint = inspector.get_pk_constraint(table_name)
        pk_columns = set(pk_constraint.get("constrained_columns", []))

        columns = [
            ColumnInfo(
                name=col["name"],
                type=str(col["type"]),
                nullable=col["nullable"],
                is_primary_key=col["name"] in pk_columns,
            )
            for col in inspector.get_columns(table_name)
        ]

        foreign_keys = [
            ForeignKeyInfo(
                column=fk["constrained_columns"][0],
                references_table=fk["referred_table"],
                references_column=fk["referred_columns"][0],
            )
            for fk in inspector.get_foreign_keys(table_name)
        ]

        tables.append(TableInfo(name=table_name, columns=columns, foreign_keys=foreign_keys))

    return tables