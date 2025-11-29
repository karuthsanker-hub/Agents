"""
Export Local Database to JSON
=============================
Run this locally to export your articles and prompts to JSON files.
Then upload these files to import into Railway.

Author: Shiv Sanker
Usage: python scripts/export_local_db.py
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

def export_data():
    """Export all data from local PostgreSQL to JSON files."""
    
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/agent_db')
    print(f"Connecting to: {database_url.split('@')[1] if '@' in database_url else database_url}")
    
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Export articles
        print("\n📚 Exporting articles...")
        cur.execute("SELECT * FROM articles ORDER BY id")
        articles = cur.fetchall()
        print(f"   Found {len(articles)} articles")
        
        # Convert to JSON-serializable format
        articles_data = []
        for article in articles:
            article_dict = dict(article)
            # Convert datetime objects to strings
            for key, value in article_dict.items():
                if isinstance(value, datetime):
                    article_dict[key] = value.isoformat()
            articles_data.append(article_dict)
        
        with open('export_articles.json', 'w', encoding='utf-8') as f:
            json.dump(articles_data, f, indent=2, ensure_ascii=False)
        print(f"   ✅ Saved to export_articles.json")
        
        # Export prompts
        print("\n📝 Exporting prompts...")
        cur.execute("SELECT * FROM prompts ORDER BY id")
        prompts = cur.fetchall()
        print(f"   Found {len(prompts)} prompts")
        
        prompts_data = []
        for prompt in prompts:
            prompt_dict = dict(prompt)
            for key, value in prompt_dict.items():
                if isinstance(value, datetime):
                    prompt_dict[key] = value.isoformat()
            prompts_data.append(prompt_dict)
        
        with open('export_prompts.json', 'w', encoding='utf-8') as f:
            json.dump(prompts_data, f, indent=2, ensure_ascii=False)
        print(f"   ✅ Saved to export_prompts.json")
        
        # Export debate cards if exists
        print("\n🃏 Exporting debate cards...")
        try:
            cur.execute("SELECT * FROM debate_cards ORDER BY id")
            cards = cur.fetchall()
            print(f"   Found {len(cards)} debate cards")
            
            cards_data = []
            for card in cards:
                card_dict = dict(card)
                for key, value in card_dict.items():
                    if isinstance(value, datetime):
                        card_dict[key] = value.isoformat()
                cards_data.append(card_dict)
            
            with open('export_debate_cards.json', 'w', encoding='utf-8') as f:
                json.dump(cards_data, f, indent=2, ensure_ascii=False)
            print(f"   ✅ Saved to export_debate_cards.json")
        except Exception as e:
            print(f"   ⚠️ No debate_cards table or error: {e}")
        
        # Export admin config if exists
        print("\n⚙️ Exporting admin config...")
        try:
            cur.execute("SELECT * FROM admin_config ORDER BY id")
            config = cur.fetchall()
            print(f"   Found {len(config)} config entries")
            
            config_data = []
            for c in config:
                c_dict = dict(c)
                for key, value in c_dict.items():
                    if isinstance(value, datetime):
                        c_dict[key] = value.isoformat()
                config_data.append(c_dict)
            
            with open('export_admin_config.json', 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            print(f"   ✅ Saved to export_admin_config.json")
        except Exception as e:
            print(f"   ⚠️ No admin_config table or error: {e}")
        
        cur.close()
        conn.close()
        
        print("\n" + "="*50)
        print("✅ Export complete!")
        print("="*50)
        print("\nFiles created:")
        print("  - export_articles.json")
        print("  - export_prompts.json")
        print("  - export_debate_cards.json (if exists)")
        print("  - export_admin_config.json (if exists)")
        print("\nNext: Run 'python scripts/import_to_railway.py' to import to Railway")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    export_data()

