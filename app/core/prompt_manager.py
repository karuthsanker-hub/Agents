"""
Prompt Manager
==============
Stores and manages AI prompts in PostgreSQL for easy customization.

Author: Shiv Sanker
Created: 2024
License: MIT
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Optional, Dict, Any, List

from app.core.config import get_settings
from app.core.logging_config import get_logger

logger = get_logger("prompts")


# Default prompts - used to seed the database
DEFAULT_PROMPTS = {
    "topic_context": {
        "name": "Topic Context",
        "description": "The debate topic and key areas for context in analysis",
        "category": "analysis",
        "content": """The 2025-2026 Policy Debate Resolution is:
"Resolved: The United States federal government should significantly increase 
its exploration and/or development of the Arctic."

Key topic areas include:
- Arctic Cod as a keystone species in the Arctic food web
- Climate change and sea ice loss impacts on Arctic ecosystems
- Shipping noise and vessel traffic impacts on marine life
- Oil spill risks and pollution threats
- Indigenous rights, food security, and co-management
- Fisheries management and precautionary moratoria
- Habitat protection and marine protected areas
- Scientific research and monitoring"""
    },
    
    "article_analysis": {
        "name": "Article Analysis Prompt",
        "description": "Main prompt for analyzing articles with GPT",
        "category": "analysis",
        "content": """You are a debate coach helping an 11th grade policy debater analyze articles for the Arctic topic.

{topic_context}

Analyze this article and extract information useful for debate. Write the summary in clear, accessible language that a high school junior would use - avoid jargon, be direct, and explain WHY this matters for debate.

ARTICLE TITLE: {title}
ARTICLE SOURCE: {source}
ARTICLE TEXT:
{text}

Provide your analysis in the following JSON format:
{{
    "title": "Article title (cleaned up if needed)",
    "author_name": "Author's full name or 'Unknown'",
    "author_credentials": "Author's title, position, expertise (if mentioned)",
    "publication_year": YYYY (integer, or null if unknown),
    "source_name": "Publication name",
    "source_type": "news|think_tank|academic|government",
    
    "summary": "Write 2-3 sentences like you're explaining to a friend: What's the main point? Why does it matter for the Arctic debate? Use simple, clear language an 11th grader would naturally use.",
    
    "key_claims": [
        "First major claim - state it clearly and simply",
        "Second major claim - what's the evidence saying?",
        "Third major claim (up to 5 total)"
    ],
    
    "side": "aff|neg|both|neutral",
    "side_confidence": 0.0-1.0,
    "side_explanation": "One sentence explaining why - does it support expanding Arctic activity (aff) or argue against it (neg)?",
    
    "topic_areas": ["area1", "area2"],
    "supports_arguments": ["What specific debate arguments can you run with this? Be specific!"],
    "against_arguments": ["What opponent arguments does this help you answer?"],
    
    "relevance_score": 1-10,
    "best_use": "When would you read this card? (e.g., '1AC Advantage 2 - Indigenous Rights', 'Neg answers to security aff')"
}}

Valid topic_areas: climate, security, economy, shipping, energy, indigenous, research, environment, military, mining, diplomacy, arctic_cod, ecosystem, food_web
Valid source_types: news, think_tank, academic, government

Respond ONLY with valid JSON, no other text."""
    },
    
    "card_tag_generation": {
        "name": "Card Tag Generation",
        "description": "Prompt for generating debate card tags/claims",
        "category": "cards",
        "content": """Generate a debate TAG for this evidence. A tag is a one-line claim that summarizes the key argument.

Rules for a good tag:
- Complete sentence stating a claim
- Active voice, present tense when possible
- Specific and impactful
- 10-20 words ideal
- Should make the argument clear even without reading the card

Context: {context}

Evidence:
{evidence}

Generate ONLY the tag line, nothing else. No quotes, no "Tag:" prefix."""
    },
    
    "card_highlighting": {
        "name": "Card Highlighting/Underlining",
        "description": "Prompt for identifying key phrases to highlight in cards",
        "category": "cards",
        "content": """Identify the 5-10 most important phrases from this evidence that should be highlighted in a debate card.

These should be the phrases that:
- Contain the strongest warrants
- Include key statistics or facts
- Make the argument clear when read alone
- A debater would read during a speech

Evidence:
{evidence}

Return ONLY a JSON array of the exact phrases, nothing else.
Format: ["phrase 1", "phrase 2", ...]"""
    },
    
    "chat_system": {
        "name": "Research Chat System Prompt",
        "description": "System prompt for the research assistant chat",
        "category": "chat",
        "content": """You are a helpful research assistant specialized in the 2025-2026 NSDA Policy Debate topic on Arctic exploration and development.

Your capabilities:
1. Answer questions about Arctic policy, environment, and debate arguments
2. Help with debate research and card cutting
3. Explain complex topics in terms an 11th grader can understand
4. Remember context from the current conversation

When given relevant memories from past conversations, use them to provide better context-aware answers.

Focus on being helpful for policy debate - that means understanding affirmative cases, negative strategies, and how evidence applies to arguments.

Always be helpful, accurate, and friendly."""
    }
}


class PromptManager:
    """
    Manages AI prompts stored in PostgreSQL.
    
    Features:
    - CRUD operations for prompts
    - Version history tracking
    - Default prompts seeding
    - Category-based organization
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._init_database()
        logger.info("PromptManager initialized")
    
    def _get_connection(self):
        """Get database connection."""
        return psycopg2.connect(self.settings.database_url)
    
    def _init_database(self):
        """Initialize prompts table."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # Main prompts table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS prompts (
                        id SERIAL PRIMARY KEY,
                        key VARCHAR(100) UNIQUE NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        category VARCHAR(50),
                        content TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Prompt history for version tracking
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS prompt_history (
                        id SERIAL PRIMARY KEY,
                        prompt_key VARCHAR(100) NOT NULL,
                        content TEXT NOT NULL,
                        changed_by VARCHAR(255),
                        changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                
                # Seed default prompts
                self._seed_default_prompts(cur, conn)
                
                logger.info("Prompts database initialized")
        except Exception as e:
            logger.error(f"Failed to init prompts database: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def _seed_default_prompts(self, cur, conn):
        """Seed default prompts if they don't exist."""
        for key, prompt_data in DEFAULT_PROMPTS.items():
            cur.execute("SELECT id FROM prompts WHERE key = %s", (key,))
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO prompts (key, name, description, category, content)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    key,
                    prompt_data['name'],
                    prompt_data.get('description', ''),
                    prompt_data.get('category', 'general'),
                    prompt_data['content']
                ))
                logger.info(f"Seeded prompt: {key}")
        conn.commit()
    
    def get_prompt(self, key: str) -> Optional[str]:
        """Get a prompt by key."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT content FROM prompts WHERE key = %s AND is_active = TRUE",
                    (key,)
                )
                row = cur.fetchone()
                return row[0] if row else None
        finally:
            conn.close()
    
    def get_prompt_full(self, key: str) -> Optional[Dict[str, Any]]:
        """Get full prompt info including metadata."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM prompts WHERE key = %s",
                    (key,)
                )
                row = cur.fetchone()
                return dict(row) if row else None
        finally:
            conn.close()
    
    def get_all_prompts(self) -> List[Dict[str, Any]]:
        """Get all prompts."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT key, name, description, category, content, 
                           is_active, updated_at
                    FROM prompts 
                    ORDER BY category, name
                """)
                return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()
    
    def get_prompts_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get prompts by category."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT key, name, description, content, is_active, updated_at
                    FROM prompts 
                    WHERE category = %s
                    ORDER BY name
                """, (category,))
                return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()
    
    def update_prompt(self, key: str, content: str, changed_by: str = None) -> bool:
        """Update a prompt and save history."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # Get current content for history
                cur.execute("SELECT content FROM prompts WHERE key = %s", (key,))
                old_row = cur.fetchone()
                
                if not old_row:
                    logger.error(f"Prompt not found: {key}")
                    return False
                
                # Save to history
                cur.execute("""
                    INSERT INTO prompt_history (prompt_key, content, changed_by)
                    VALUES (%s, %s, %s)
                """, (key, old_row[0], changed_by))
                
                # Update prompt
                cur.execute("""
                    UPDATE prompts 
                    SET content = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE key = %s
                """, (content, key))
                
                conn.commit()
                logger.info(f"Prompt updated: {key}")
                return True
        except Exception as e:
            logger.error(f"Failed to update prompt: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_prompt_history(self, key: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get version history for a prompt."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT content, changed_by, changed_at
                    FROM prompt_history 
                    WHERE prompt_key = %s
                    ORDER BY changed_at DESC
                    LIMIT %s
                """, (key, limit))
                return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()
    
    def reset_prompt(self, key: str) -> bool:
        """Reset a prompt to its default value."""
        if key not in DEFAULT_PROMPTS:
            logger.error(f"No default for prompt: {key}")
            return False
        
        return self.update_prompt(
            key, 
            DEFAULT_PROMPTS[key]['content'],
            changed_by="system_reset"
        )


# Singleton instance
_prompt_manager: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    """Get singleton PromptManager instance."""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager

