"""
Delete articles whose source URLs are inaccessible (HTTP 403/404, paywalled, or no text).

Usage:
    python scripts/remove_inaccessible_articles.py
    railway run --service Postgres python scripts/remove_inaccessible_articles.py
"""

import asyncio
import os
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

database_url_env = os.environ.get("DATABASE_URL")
public_url_env = os.environ.get("DATABASE_PUBLIC_URL")
if (
    database_url_env
    and "railway.internal" in database_url_env
    and public_url_env
):
    os.environ["DATABASE_URL"] = public_url_env

from app.debate.article_analyzer import ArticleAnalyzer


def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL environment variable is required")

    analyzer = ArticleAnalyzer()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    conn = psycopg2.connect(database_url)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT id, url, title FROM articles ORDER BY id;")
    rows = cur.fetchall()

    deleted = 0
    kept = 0

    for row in rows:
        article_id = row["id"]
        url = row["url"]
        try:
            fetch_result = loop.run_until_complete(analyzer.fetch_article(url))
            text = (fetch_result.get("text") or "").strip()
            has_error = bool(fetch_result.get("error"))
            paywalled = fetch_result.get("is_paywalled")

            if has_error or paywalled or len(text) < 200:
                cur.execute("DELETE FROM articles WHERE id = %s", (article_id,))
                deleted += 1
                reason = (
                    fetch_result.get("error")
                    or ("paywalled" if paywalled else "insufficient content")
                )
                print(f"Deleted article {article_id} ({row['title'] or url}): {reason}")
            else:
                kept += 1
        except Exception as exc:
            cur.execute("DELETE FROM articles WHERE id = %s", (article_id,))
            deleted += 1
            print(f"Deleted article {article_id} ({row['title'] or url}): fetch exception {exc}")

    cur.close()
    conn.close()
    loop.close()

    print(f"Cleanup complete. Deleted {deleted}, kept {kept}.")


if __name__ == "__main__":
    main()

