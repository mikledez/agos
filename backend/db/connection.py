import os
from pathlib import Path
from psycopg_pool import ConnectionPool
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("AGOS_DATABASE_URL")

pool: ConnectionPool | None = None

def get_pool() -> ConnectionPool:
    global pool
    if pool is None:
        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL / AGOS_DATABASE_URL not set")
        pool = ConnectionPool(
            conninfo=DATABASE_URL,
            kwargs={"autocommit": False},
            open=False,
            check=ConnectionPool.check_connection,
        )
        pool.open()
    return pool

def close_pool() -> None:
    global pool
    if pool is not None:
        pool.close()
        pool = None

def get_conn():
    with get_pool().connection() as conn:
        yield conn
