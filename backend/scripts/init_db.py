import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.init import init_db

def main() -> None:
    dsn = sys.argv[1] if len(sys.argv) > 1 else None
    init_db(dsn)
    print("Database initialized.")

if __name__ == "__main__":
    main()
