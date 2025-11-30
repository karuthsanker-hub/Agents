"""
Populate evidence excerpt/context for all articles that are missing them.

Usage:
    python scripts/backfill_evidence.py
    railway run python scripts/backfill_evidence.py   # for Railway Postgres
"""

import json
import os
import sys
from pathlib import Path

import asyncio

import psycopg2
from psycopg2.extras import RealDictCursor

# Ensure project root on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Normalize DATABASE_URL before importing project modules that read settings
database_url_env = os.environ.get("DATABASE_URL")
public_url_env = os.environ.get("DATABASE_PUBLIC_URL")
if (
    database_url_env
    and "railway.internal" in database_url_env
    and public_url_env
):
    os.environ["DATABASE_URL"] = public_url_env

from app.debate.card_formatter import get_card_formatter
from app.debate.article_analyzer import ArticleAnalyzer


def stringify_claims(key_claims):
    if not key_claims:
        return ""
    if isinstance(key_claims, str):
        try:
            key_claims = json.loads(key_claims)
        except json.JSONDecodeError:
            return key_claims
    if isinstance(key_claims, list):
        return " ".join(str(k) for k in key_claims if k)
    return str(key_claims)


def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL environment variable is required")

    formatter = get_card_formatter()
    analyzer = ArticleAnalyzer()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    conn = psycopg2.connect(database_url)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT id, title, summary, key_claims, full_text, url,
               evidence_excerpt, evidence_context
        FROM articles
        """
    )

    rows = cur.fetchall()
    updated = 0
    skipped = 0

    for row in rows:
        if row.get("evidence_context") and row.get("evidence_excerpt"):
            skipped += 1
            continue

        full_text = (row.get("full_text") or "").strip()
        if len(full_text) < 200 and row.get("url"):
            try:
                fetch_result = loop.run_until_complete(
                    analyzer.fetch_article(row["url"])
                )
                fetched_text = (fetch_result.get("text") or "").strip()
                if fetch_result.get("error"):
                    print(
                        f"Fetch reported error for article {row['id']}: {fetch_result.get('error')}"
                    )
                if len(fetched_text) >= 200:
                    full_text = fetched_text
                    cur.execute(
                        "UPDATE articles SET full_text = %s WHERE id = %s",
                        (full_text, row["id"]),
                    )
                    print(
                        f"Fetched {len(fetched_text)} chars for article {row['id']}"
                    )
                else:
                    print(
                        f"Fetched insufficient content for article {row['id']} (len={len(fetched_text)})"
                    )
            except Exception as fetch_error:
                print(f"Fetch failed for article {row['id']}: {fetch_error}")
        if len(full_text) < 200:
            skipped += 1
            continue

        claim_text = " ".join(
            filter(
                None,
                [
                    row.get("summary", ""),
                    stringify_claims(row.get("key_claims")),
                ],
            )
        ).strip()

        passage = formatter.extract_evidence_passage(
            original_content=full_text,
            claim_or_summary=claim_text or full_text[:500],
        )

        evidence_excerpt = passage.get("passage")
        evidence_context = passage.get("context_passage") or evidence_excerpt

        if not evidence_excerpt or not evidence_context:
            skipped += 1
            continue

        cur.execute(
            """
            UPDATE articles
            SET evidence_excerpt = %s,
                evidence_context = %s,
                processed_at = processed_at
            WHERE id = %s
            """,
            (
                evidence_excerpt,
                evidence_context,
                row["id"],
            ),
        )
        updated += 1

    cur.close()
    conn.close()
    loop.close()

    print(f"Backfill complete. Updated {updated} articles, skipped {skipped}.")


if __name__ == "__main__":
    main()

