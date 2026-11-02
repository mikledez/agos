#!/usr/bin/env python3
"""Print a safe Postgres connectivity/schema check (no secrets)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.connection import close_pool, get_pool


def main() -> None:
    try:
        with get_pool().connection() as conn:
            database, user = conn.execute(
                "SELECT current_database(), current_user"
            ).fetchone()
            version = conn.execute("SHOW server_version").fetchone()[0]
            tables = conn.execute(
                """
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
                """
            ).fetchall()
            users = conn.execute("SELECT count(*) FROM users").fetchone()[0]
            images = conn.execute("SELECT count(*) FROM images").fetchone()[0]

        print(f"database={database} user={user} server={version}")
        print(f"tables={', '.join(row[0] for row in tables) or '(none)'}")
        print(f"users={users} images={images}")
    finally:
        close_pool()


if __name__ == "__main__":
    main()
