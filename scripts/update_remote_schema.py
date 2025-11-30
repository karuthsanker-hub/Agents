"""
Utility script to run database schema updates against the configured DATABASE_URL.

Usage:
    railway run python scripts/update_remote_schema.py
"""

import os

import psycopg2


def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is not set")

    conn = psycopg2.connect(database_url)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute(
        """
        ALTER TABLE articles
        ADD COLUMN IF NOT EXISTS evidence_excerpt TEXT;
        """
    )
    cur.execute(
        """
        ALTER TABLE articles
        ADD COLUMN IF NOT EXISTS evidence_context TEXT;
        """
    )

    cur.close()
    conn.close()
    print("Schema update complete: evidence columns ensured.")


if __name__ == "__main__":
    main()

