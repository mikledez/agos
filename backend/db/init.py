from __future__ import annotations

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from .connection import DATABASE_URL
from .schema import SCHEMA_PATH

def ensure_database(dsn: str | None = None) -> bool:

    dsn = dsn or DATABASE_URL
    if not dsn:
        raise RuntimeError("DATABASE_URL / AGOS_DATABASE_URL not set")

    params = conninfo_to_dict(dsn)
    dbname = params.get("dbname")
    if not dbname:
        return False

    maintenance = {**params, "dbname": "postgres"}
    try:
        conn = psycopg.connect(make_conninfo(**maintenance), autocommit=True)
    except psycopg.Error:
        return False

    with conn:
        exists = conn.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (dbname,)
        ).fetchone()
        if exists:
            return False
        conn.execute(
            sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname))
        )
        return True

def apply_schema(dsn: str | None = None) -> None:

    dsn = dsn or DATABASE_URL
    if not dsn:
        raise RuntimeError("DATABASE_URL / AGOS_DATABASE_URL not set")

    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute(SCHEMA_PATH.read_text())

def init_db(dsn: str | None = None) -> None:

    ensure_database(dsn)
    apply_schema(dsn)
