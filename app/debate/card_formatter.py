"""
Debate Card Formatter
=====================
Converts evidence into proper CX Policy Debate card format.
Supports tag generation, citation formatting, and card text highlighting.

Prompts are stored in the database and can be customized via Admin panel.

Author: Shiv Sanker
"""

import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from openai import OpenAI

from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.core.admin_config import get_admin_config
from app.core.prompt_manager import get_prompt_manager

logger = get_logger("debate.cards")


class CardFormatter:
    """Formats evidence into debate cards using AI."""
    
    # Default prompts (fallback if database is unavailable)
    DEFAULT_TAG_PROMPT = """Generate a debate TAG for this evidence. A tag is a one-line claim that summarizes the key argument.

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

    DEFAULT_HIGHLIGHT_PROMPT = """Identify the 5-10 most important phrases from this evidence that should be highlighted in a debate card.

These should be the phrases that:
- Contain the strongest warrants
- Include key statistics or facts
- Make the argument clear when read alone
- A debater would read during a speech

Evidence:
{evidence}

Return ONLY a JSON array of the exact phrases, nothing else.
Format: ["phrase 1", "phrase 2", ...]"""
    
    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.admin_config = get_admin_config()
        self.prompt_manager = get_prompt_manager()
        logger.info("CardFormatter initialized")
    
    def _get_tag_prompt(self) -> str:
        """Get tag generation prompt from database or fallback."""
        db_prompt = self.prompt_manager.get_prompt("card_tag_generation")
        return db_prompt if db_prompt else self.DEFAULT_TAG_PROMPT
    
    def _get_highlight_prompt(self) -> str:
        """Get highlighting prompt from database or fallback."""
        db_prompt = self.prompt_manager.get_prompt("card_highlighting")
        return db_prompt if db_prompt else self.DEFAULT_HIGHLIGHT_PROMPT
    
    def format_citation(
        self,
        author: str,
        year: str,
        title: str,
        source: str,
        url: Optional[str] = None,
        qualifications: Optional[str] = None
    ) -> str:
        """
        Format a proper debate citation.
        
        Format: LastName YY (quals) - Title, Source
        """
        # Extract last name if full name given
        author_parts = author.strip().split()
        if "et al" in author.lower():
            last_name = author.split()[0]
            last_name = f"{last_name} et al."
        elif author_parts:
            last_name = author_parts[-1].rstrip(',.')
        else:
            last_name = "Unknown"
        
        # Format year as 2-digit
        year_str = str(year)[-2:] if year else "??"
        
        # Build citation
        cite_parts = [f"{last_name} {year_str}"]
        
        if qualifications:
            cite_parts.append(f"({qualifications})")
        
        cite_line = " ".join(cite_parts)
        
        # Add source line
        source_line = f"{title}"
        if source and source != title:
            source_line += f", {source}"
        if url:
            source_line += f"\n{url}"
        
        return f"{cite_line}\n{source_line}"
    
    def generate_tag(self, evidence_text: str, argument_context: Optional[str] = None) -> str:
        """
        Generate a debate tag (one-line claim) for evidence using AI.
        
        A good tag:
        - States a complete claim
        - Uses active voice
        - Is specific and impactful
        - Usually 10-20 words
        """
        context = argument_context or "policy debate"
        
        # Get prompt from database (customizable via Admin panel)
        prompt_template = self._get_tag_prompt()
        prompt = prompt_template.format(
            context=context,
            evidence=evidence_text[:2000]
        )

        # Check rate limits
        rate_check = self.admin_config.check_rate_limit()
        if not rate_check.get('allowed', True):
            logger.warning(f"Rate limit exceeded: {rate_check.get('reason')}")
            return "Evidence supports the argument [Rate limit exceeded]"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=100,
                temperature=0.3
            )
            tag = response.choices[0].message.content.strip()
            
            # Track usage
            tokens_used = response.usage.total_tokens if response.usage else 100
            self.admin_config.track_usage(
                endpoint="card_format_tag",
                tokens_used=tokens_used,
                model=self.model
            )
            
            # Clean up
            tag = tag.strip('"\'')
            if tag.lower().startswith("tag:"):
                tag = tag[4:].strip()
            return tag
        except Exception as e:
            logger.error(f"Tag generation error: {e}")
            return "Evidence supports the argument"
    
    def highlight_card(self, full_text: str, key_phrases: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Generate highlighted/underlined version of card text.
        
        Returns both the full text and a highlighted version with key phrases marked.
        In debate, underlining shows what to read; highlighting shows the most critical parts.
        """
        if not key_phrases:
            # Get prompt from database (customizable via Admin panel)
            prompt_template = self._get_highlight_prompt()
            prompt = prompt_template.format(evidence=full_text[:3000])
            
            # Check rate limits
            rate_check = self.admin_config.check_rate_limit()
            if not rate_check.get('allowed', True):
                logger.warning(f"Rate limit exceeded: {rate_check.get('reason')}")
                key_phrases = []
            else:
                try:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        max_completion_tokens=500,
                        temperature=0.2
                    )
                    import json
                    key_phrases = json.loads(response.choices[0].message.content.strip())
                    
                    # Track usage
                    tokens_used = response.usage.total_tokens if response.usage else 300
                    self.admin_config.track_usage(
                        endpoint="card_format_highlight",
                        tokens_used=tokens_used,
                        model=self.model
                    )
                except:
                    key_phrases = []
        
        # Mark key phrases with underline markers
        highlighted = full_text
        for phrase in key_phrases:
            if phrase in highlighted:
                highlighted = highlighted.replace(phrase, f"__{phrase}__")
        
        return {
            "full_text": full_text,
            "highlighted": highlighted,
            "key_phrases": key_phrases
        }
    
    def format_card(
        self,
        evidence_text: str,
        author: str,
        year: str,
        title: str,
        source: str,
        url: Optional[str] = None,
        qualifications: Optional[str] = None,
        argument_context: Optional[str] = None,
        generate_tag: bool = True,
        highlight: bool = True
    ) -> Dict[str, Any]:
        """
        Format complete debate card with tag, cite, and highlighted text.
        
        Returns:
            {
                "tag": "One-line claim",
                "cite": "Author YY - Title, Source",
                "card_text": "The evidence...",
                "highlighted_text": "The __evidence__...",
                "key_phrases": ["evidence", ...],
                "full_card": "Complete formatted card"
            }
        """
        logger.info(f"Formatting card: {author} {year}")
        
        # Generate citation
        cite = self.format_citation(author, year, title, source, url, qualifications)
        
        # Generate tag if requested
        if generate_tag:
            tag = self.generate_tag(evidence_text, argument_context)
        else:
            tag = ""
        
        # Highlight if requested
        if highlight:
            highlight_data = self.highlight_card(evidence_text)
            highlighted_text = highlight_data["highlighted"]
            key_phrases = highlight_data["key_phrases"]
        else:
            highlighted_text = evidence_text
            key_phrases = []
        
        # Build full card
        full_card_parts = []
        if tag:
            full_card_parts.append(f"**{tag}**")
        full_card_parts.append(f"\n{cite}\n")
        full_card_parts.append(highlighted_text)
        
        full_card = "\n".join(full_card_parts)
        
        return {
            "tag": tag,
            "cite": cite,
            "card_text": evidence_text,
            "highlighted_text": highlighted_text,
            "key_phrases": key_phrases,
            "full_card": full_card
        }
    
    def extract_cards_from_document(
        self,
        document_text: str,
        topic_context: str = "Arctic policy debate",
        side: str = "aff",
        max_cards: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Extract multiple debate cards from a longer document.
        
        Uses AI to identify the best quotable sections and format them as cards.
        """
        logger.info(f"Extracting up to {max_cards} cards from document")
        
        prompt = f"""You are a Policy Debate coach helping extract cards from a document.

Topic context: {topic_context}
Side: {side.upper()} ({"supports the resolution" if side == "aff" else "opposes the resolution"})

Document text:
{document_text[:8000]}

Extract up to {max_cards} debate cards from this document. For each card, identify:
1. The best quotable passage (50-200 words)
2. A tag (one-line claim summarizing the argument)
3. What advantage/disadvantage this supports

Return as JSON array:
[
  {{
    "passage": "The exact quote...",
    "tag": "One-line claim",
    "argument_type": "Advantage 1: Ecosystem" or "Impact: Biodiversity" etc.,
    "author_hint": "Lastname YYYY if visible"
  }}
]

Only return the JSON array, nothing else."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=2000,
                temperature=0.3
            )
            
            import json
            cards_data = json.loads(response.choices[0].message.content.strip())
            
            # Format each extracted card
            formatted_cards = []
            for card in cards_data[:max_cards]:
                formatted = {
                    "tag": card.get("tag", ""),
                    "passage": card.get("passage", ""),
                    "argument_type": card.get("argument_type", ""),
                    "author_hint": card.get("author_hint", ""),
                    "needs_cite": True  # Flag that citation needs to be added
                }
                formatted_cards.append(formatted)
            
            logger.info(f"Extracted {len(formatted_cards)} cards")
            return formatted_cards
            
        except Exception as e:
            logger.error(f"Card extraction error: {e}")
            return []


# Singleton instance
_card_formatter = None

def get_card_formatter() -> CardFormatter:
    """Get singleton CardFormatter instance."""
    global _card_formatter
    if _card_formatter is None:
        _card_formatter = CardFormatter()
    return _card_formatter

