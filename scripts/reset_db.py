"""
DANGER: wipes EVERYTHING in the database — all tables, all data,
including Alembic's version history. Only safe now because the database
contains nothing but demo seed data.

Run with:  python scripts/reset_db.py
Then:      alembic revision --autogenerate -m "v1 schema"
           alembic upgrade head
           python scripts/seed.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import engine


def reset():
    answer = input(
        "This will DELETE ALL TABLES AND DATA in the database.\n"
        "Type YES (in capitals) to continue: "
    )
    if answer.strip() != "YES":
        print("Aborted. Nothing was changed.")
        return

    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    print("Database wiped clean. Now run:")
    print('  alembic revision --autogenerate -m "v1 schema"')
    print("  alembic upgrade head")
    print("  python scripts/seed.py")


if __name__ == "__main__":
    reset()
