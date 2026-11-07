#!/usr/bin/env python3
"""Delete image records whose files were lost before images moved to the database.

Run once, after the database-storage release is deployed. Without --yes it only
reports what would be deleted.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import repository as repo
from db.connection import close_pool, get_pool


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--yes", action="store_true", help="delete the records instead of counting"
    )
    args = parser.parse_args()

    try:
        with get_pool().connection() as conn:
            database = conn.execute("SELECT current_database()").fetchone()[0]
        print(f"database={database}")

        if args.yes:
            print(f"deleted {repo.delete_images_without_files()} image records")
        else:
            print(f"would delete {repo.count_images_without_files()} image records")
            print("run again with --yes to delete them")
    finally:
        close_pool()


if __name__ == "__main__":
    main()
