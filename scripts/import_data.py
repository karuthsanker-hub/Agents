"""
Import Data to Database
=======================
Imports data from JSON export files into the database.
Works with both local and Railway databases.

Author: Shiv Sanker
Usage: 
  Local:   python scripts/import_data.py
  Railway: railway run python scripts/import_data.py
"""

import json
import os
import sys
from datetime import datetime

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import psycopg2
from psycopg2.extras import RealDictCursor

def import_data():
    """Import data from JSON files into the database."""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not set!")
        return
    
    # Hide password in output
    display_url = database_url.split('@')[1] if '@' in database_url else database_url
    print(f"Connecting to: {display_url}")
    
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Import articles
        if os.path.exists('export_articles.json'):
            print("\n📚 Importing articles...")
            with open('export_articles.json', 'r', encoding='utf-8') as f:
                articles = json.load(f)
            
            # Ensure table exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id SERIAL PRIMARY KEY,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT,
                    author TEXT,
                    publication_year TEXT,
                    source TEXT,
                    summary TEXT,
                    argument_type TEXT,
                    full_text TEXT,
                    is_paywalled BOOLEAN DEFAULT FALSE,
                    fetch_status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            imported = 0
            skipped = 0
            for article in articles:
                try:
                    cur.execute("""
                        INSERT INTO articles (url, title, author, publication_year, source, 
                                            summary, argument_type, full_text, is_paywalled, 
                                            fetch_status, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (url) DO NOTHING
                    """, (
                        article.get('url'),
                        article.get('title'),
                        article.get('author'),
                        article.get('publication_year'),
                        article.get('source'),
                        article.get('summary'),
                        article.get('argument_type'),
                        article.get('full_text'),
                        article.get('is_paywalled', False),
                        article.get('fetch_status', 'pending'),
                        article.get('created_at'),
                        article.get('updated_at')
                    ))
                    if cur.rowcount > 0:
                        imported += 1
                    else:
                        skipped += 1
                except Exception as e:
                    print(f"   ⚠️ Error importing article: {e}")
                    skipped += 1
            
            print(f"   ✅ Imported {imported} articles, skipped {skipped} duplicates")
        
        # Import prompts
        if os.path.exists('export_prompts.json'):
            print("\n📝 Importing prompts...")
            with open('export_prompts.json', 'r', encoding='utf-8') as f:
                prompts = json.load(f)
            
            # Ensure table exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS prompts (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    prompt_text TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            imported = 0
            skipped = 0
            for prompt in prompts:
                try:
                    cur.execute("""
                        INSERT INTO prompts (name, description, prompt_text, category, 
                                           is_active, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (name) DO UPDATE SET
                            prompt_text = EXCLUDED.prompt_text,
                            description = EXCLUDED.description,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        prompt.get('name'),
                        prompt.get('description'),
                        prompt.get('prompt_text'),
                        prompt.get('category', 'general'),
                        prompt.get('is_active', True),
                        prompt.get('created_at'),
                        prompt.get('updated_at')
                    ))
                    imported += 1
                except Exception as e:
                    print(f"   ⚠️ Error importing prompt: {e}")
                    skipped += 1
            
            print(f"   ✅ Imported/updated {imported} prompts")
        
        # Import debate cards
        if os.path.exists('export_debate_cards.json'):
            print("\n🃏 Importing debate cards...")
            with open('export_debate_cards.json', 'r', encoding='utf-8') as f:
                cards = json.load(f)
            
            # Ensure table exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS debate_cards (
                    id SERIAL PRIMARY KEY,
                    article_id INTEGER REFERENCES articles(id),
                    tag TEXT,
                    cite TEXT,
                    card_body TEXT,
                    highlighted_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            imported = 0
            for card in cards:
                try:
                    cur.execute("""
                        INSERT INTO debate_cards (article_id, tag, cite, card_body, 
                                                highlighted_text, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        card.get('article_id'),
                        card.get('tag'),
                        card.get('cite'),
                        card.get('card_body'),
                        card.get('highlighted_text'),
                        card.get('created_at')
                    ))
                    imported += 1
                except Exception as e:
                    print(f"   ⚠️ Error importing card: {e}")
            
            print(f"   ✅ Imported {imported} debate cards")
        
        cur.close()
        conn.close()
        
        print("\n" + "="*50)
        print("✅ Import complete!")
        print("="*50)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    import_data()

