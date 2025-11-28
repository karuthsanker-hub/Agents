"""
Restore Articles from Backup
============================
Restores articles from a JSON backup file.

Usage:
    python scripts/restore_articles.py backups/articles_backup_YYYYMMDD_HHMMSS.json

Author: Shiv Sanker
"""

import sys
import json
import psycopg2
from datetime import datetime

def restore_articles(backup_file: str, db_url: str = "postgresql://postgres:postgres@localhost:5432/agent_db"):
    """Restore articles from a JSON backup file."""
    
    print(f"Loading backup from: {backup_file}")
    
    with open(backup_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    articles = data['articles']
    print(f"Found {len(articles)} articles in backup")
    print(f"Backup date: {data.get('backup_date', 'unknown')}")
    
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cur = conn.cursor()
    
    # Clear existing articles
    print("\nClearing existing articles...")
    cur.execute("DELETE FROM articles")
    
    # Insert backed up articles
    print("Restoring articles...")
    restored = 0
    
    for article in articles:
        try:
            cur.execute("""
                INSERT INTO articles (
                    id, url, title, source_name, source_type, author_name,
                    publication_year, summary, key_claims, side, side_confidence,
                    topic_areas, arguments_supported, arguments_opposed,
                    relevance_score, is_processed, is_paywalled, cards_cut,
                    discovered_at
                ) VALUES (
                    %(id)s, %(url)s, %(title)s, %(source_name)s, %(source_type)s,
                    %(author_name)s, %(publication_year)s, %(summary)s, %(key_claims)s,
                    %(side)s, %(side_confidence)s, %(topic_areas)s,
                    %(arguments_supported)s, %(arguments_opposed)s, %(relevance_score)s,
                    %(is_processed)s, %(is_paywalled)s, %(cards_cut)s, %(discovered_at)s
                )
            """, article)
            restored += 1
        except Exception as e:
            print(f"  Error restoring article {article.get('id')}: {e}")
    
    # Reset sequence
    cur.execute("SELECT setval('articles_id_seq', (SELECT MAX(id) FROM articles))")
    
    conn.close()
    
    print(f"\n✅ Restored {restored}/{len(articles)} articles")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/restore_articles.py <backup_file.json>")
        print("\nAvailable backups:")
        import os
        if os.path.exists("backups"):
            for f in sorted(os.listdir("backups")):
                if f.endswith('.json'):
                    print(f"  - backups/{f}")
        sys.exit(1)
    
    restore_articles(sys.argv[1])

