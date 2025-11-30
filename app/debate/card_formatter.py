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
from typing import Optional, Dict, Any, List, Tuple
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

    DEFAULT_PASSAGE_EXTRACTION_PROMPT = """You are helping extract the EXACT ORIGINAL TEXT from a source document for a debate card.

CLAIM TO SUPPORT: {claim}

ORIGINAL SOURCE DOCUMENT:
{source_text}

TASK: Find the passage in the ORIGINAL SOURCE that best supports this claim.

RULES:
1. Extract VERBATIM text from the source - do NOT paraphrase or summarize
2. Include 2-3 sentences BEFORE the key point for context
3. Include 2-3 sentences AFTER the key point for context  
4. The passage should be 50-300 words (ideal for a debate card)
5. The extracted text must appear EXACTLY in the source document

Return JSON:
{{
    "passage": "The exact verbatim text from the source...",
    "start_context": "Brief note on what comes before",
    "relevance": "Why this passage supports the claim"
}}

Return ONLY valid JSON, nothing else."""
    
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
    
    def _get_passage_extraction_prompt(self) -> str:
        """Get passage extraction prompt from database or fallback."""
        db_prompt = self.prompt_manager.get_prompt("passage_extraction")
        return db_prompt if db_prompt else self.DEFAULT_PASSAGE_EXTRACTION_PROMPT
    
    def extract_evidence_passage(
        self, 
        original_content: str, 
        claim_or_summary: str
    ) -> Dict[str, Any]:
        """
        Extract the actual author's text that supports a claim.
        
        This finds the most relevant passage from the ORIGINAL source
        (not AI-generated summary) and extracts it with context.
        
        Args:
            original_content: The full text fetched from the source URL
            claim_or_summary: The AI summary or claim to find evidence for
            
        Returns:
            {
                "passage": "Verbatim text from source...",
                "start_context": "What comes before",
                "relevance": "Why this supports the claim",
                "success": True/False
            }
        """
        logger.info("Extracting evidence passage from original source")
        
        if not original_content or len(original_content.strip()) < 100:
            logger.warning("Original content too short for extraction")
            return {
                "passage": "",
                "start_context": "",
                "relevance": "",
                "success": False,
                "error": "Source content too short"
            }
        
        # Check rate limits
        rate_check = self.admin_config.check_rate_limit()
        if not rate_check.get('allowed', True):
            logger.warning(f"Rate limit exceeded: {rate_check.get('reason')}")
            return {
                "passage": original_content[:500],
                "start_context": "Rate limit - using first 500 chars",
                "relevance": "Automatic fallback",
                "success": False,
                "error": rate_check.get('reason')
            }
        
        # Get prompt and format it
        prompt_template = self._get_passage_extraction_prompt()
        prompt = prompt_template.format(
            claim=claim_or_summary[:500],
            source_text=original_content[:6000]  # Limit to ~6k chars
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=1000,
                temperature=0.2  # Low temp for accuracy
            )
            
            import json
            result = json.loads(response.choices[0].message.content.strip())
            
            # Track usage
            tokens_used = response.usage.total_tokens if response.usage else 500
            self.admin_config.track_usage(
                endpoint="extract_evidence_passage",
                tokens_used=tokens_used,
                model=self.model
            )
            
            passage = result.get("passage", "")
            passage_start = original_content.find(passage) if passage else -1
            
            # Verify the passage actually exists in original content
            if passage and passage_start == -1:
                logger.warning("Extracted passage not found verbatim in source - trying fuzzy match")
                # Try to find a close match
                fuzzy_match, fuzzy_start = self._find_similar_passage(passage, original_content)
                passage = fuzzy_match
                passage_start = fuzzy_start
            
            context_passage = self._build_context_passage(
                original_content,
                passage,
                passage_start,
                sentences_before=2,
                sentences_after=2
            )
            
            return {
                "passage": passage,
                "context_passage": context_passage,
                "start_context": result.get("start_context", ""),
                "relevance": result.get("relevance", ""),
                "success": bool(passage)
            }
            
        except Exception as e:
            logger.error(f"Passage extraction error: {e}")
            # Fallback: return first relevant chunk
            fallback_passage = original_content[:500]
            context_passage = self._build_context_passage(
                original_content,
                fallback_passage,
                0,
                sentences_before=0,
                sentences_after=2
            )
            return {
                "passage": fallback_passage,
                "context_passage": context_passage,
                "start_context": "Extraction failed - using start of document",
                "relevance": "Automatic fallback",
                "success": False,
                "error": str(e)
            }
    
    def _find_similar_passage(self, target: str, source: str, threshold: int = 50) -> Tuple[str, int]:
        """
        Find the most similar passage in source to target text.
        
        Returns the passage and its starting index.
        """
        target_words = set(w.lower() for w in target.split() if len(w) > 3)
        if not target_words:
            return "", -1
        
        source_words = source.split()
        best_match = ""
        best_score = 0
        best_start = -1
        window_size = max(len(target.split()), 10)
        
        for i in range(len(source_words) - window_size + 1):
            window = source_words[i:i + window_size]
            window_set = set(w.lower() for w in window if len(w) > 3)
            overlap = len(target_words & window_set)
            score = overlap / len(target_words) * 100
            
            if score > best_score and score >= threshold:
                best_score = score
                start_word_index = max(0, i - 20)
                end_word_index = min(len(source_words), i + window_size + 20)
                best_match = " ".join(source_words[start_word_index:end_word_index])
                
                # Approximate original character index
                char_index = len(" ".join(source_words[:start_word_index]))
                best_start = char_index
        
        return best_match, best_start
    
    def _build_context_passage(
        self,
        source_text: str,
        passage: str,
        passage_start: int,
        sentences_before: int = 2,
        sentences_after: int = 2
    ) -> str:
        """
        Build a contextual passage with sentences before and after the key passage.
        """
        if not passage:
            return ""
        
        if passage_start < 0:
            passage_start = source_text.find(passage)
        if passage_start < 0:
            passage_start = 0
        
        sentence_pattern = re.compile(r'[^.!?]*[.!?]|[^.!?]+$')
        sentences = [(match.group().strip(), match.start(), match.end()) for match in sentence_pattern.finditer(source_text)]
        
        if not sentences:
            return passage
        
        passage_sentence_index = None
        for idx, (_, start, end) in enumerate(sentences):
            if start <= passage_start < end:
                passage_sentence_index = idx
                break
        
        if passage_sentence_index is None:
            # Fallback to simple window
            start_idx = max(0, passage_start - 400)
            end_idx = min(len(source_text), passage_start + len(passage) + 400)
            context = source_text[start_idx:end_idx]
            return context.strip()
        
        start_sentence = max(0, passage_sentence_index - sentences_before)
        end_sentence = min(len(sentences), passage_sentence_index + sentences_after + 1)
        
        context_sentences = [sentences[i][0] for i in range(start_sentence, end_sentence)]
        context_text = " ".join(context_sentences).strip()
        
        if passage not in context_text and passage.strip():
            context_text = f"{context_text}\n{passage}" if context_text else passage
        
        return context_text.strip()
    
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
    
    def _mark_phrase(self, text: str, phrase: str) -> Tuple[str, bool]:
        """Underline phrase in text (case-insensitive, first occurrence only)."""
        if not phrase:
            return text, False
        phrase = phrase.strip()
        if not phrase:
            return text, False
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        match = pattern.search(text)
        if not match:
            return text, False
        start, end = match.span()
        marked = text[:start] + f"__{text[start:end]}__" + text[end:]
        return marked, True
    
    def highlight_card(
        self,
        full_text: str,
        key_phrases: Optional[List[str]] = None,
        focus_passage: Optional[str] = None
    ) -> Dict[str, str]:
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
        
        highlighted = full_text
        
        # Always emphasize the primary passage (case-insensitive)
        if focus_passage:
            highlighted, matched = self._mark_phrase(highlighted, focus_passage)
            if not matched and len(highlighted) > 0:
                # fallback: highlight first sentence if passage not found
                first_sentence = highlighted.split('\n')[0][:300]
                highlighted, _ = self._mark_phrase(highlighted, first_sentence)
        
        for phrase in key_phrases:
            highlighted, _ = self._mark_phrase(highlighted, phrase)
        
        return {
            "full_text": full_text,
            "highlighted": highlighted,
            "key_phrases": key_phrases or []
        }
    
    def format_card(
        self,
        evidence_text: str,
        author: str,
        year: str,
        title: str,
        source: str,
        focus_passage: Optional[str] = None,
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
            highlight_data = self.highlight_card(
                evidence_text,
                focus_passage=focus_passage
            )
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
            "focus_passage": focus_passage,
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

