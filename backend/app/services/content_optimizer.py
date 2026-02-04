"""
Content Optimizer for Token-Constrained Analysis

Maximizes information density within Groq's 6000 TPM free tier limit.
Strategies:
1. Key insight extraction before truncation
2. Priority-based content selection
3. Efficient formatting (bullet points > prose)
4. Deduplication of redundant information
"""

from typing import List, Dict, Any, Tuple, Optional
import re


# Approximate token calculation (1 token ≈ 4 chars for English)
def estimate_tokens(text: str) -> int:
    """Estimate token count for a text string."""
    return len(text) // 4


def tokens_to_chars(tokens: int) -> int:
    """Convert token budget to character budget."""
    return tokens * 4


class ContentOptimizer:
    """
    Optimizes content for maximum information within token limits.
    """

    # Keywords that indicate high-value sentences
    HIGH_VALUE_PATTERNS = [
        # Financial metrics
        r'revenue\s+(?:of\s+)?(?:rm|myr|usd|\$)?\s*[\d,.]+',
        r'profit\s+(?:of\s+)?(?:rm|myr|usd|\$)?\s*[\d,.]+',
        r'(?:grew|increased|decreased|fell|dropped|rose)\s+(?:by\s+)?[\d.]+\s*%',
        r'(?:q[1-4]|quarter)\s+\d{4}',
        r'dividend\s+(?:of\s+)?(?:rm|myr|usd|\$)?\s*[\d,.]+',
        r'eps\s+(?:of\s+)?(?:rm|myr|usd|\$)?\s*[\d,.]+',

        # Corporate events
        r'(?:acquire|acquisition|merger|takeover)',
        r'(?:ceo|cfo|chairman|director)\s+(?:appoint|resign|step)',
        r'(?:ipo|listing|delist)',
        r'(?:lawsuit|legal|court|fine|penalty)',

        # ESG
        r'(?:net\s+zero|carbon\s+neutral|sustainability)',
        r'(?:esg|governance|compliance)',
        r'(?:emission|scope\s+[123])',

        # Ratings/Analysis
        r'(?:rating|outlook|forecast|guidance)',
        r'(?:buy|sell|hold|overweight|underweight)',
        r'(?:target\s+price|price\s+target)',
    ]

    def __init__(self):
        self.high_value_regex = re.compile(
            '|'.join(self.HIGH_VALUE_PATTERNS),
            re.IGNORECASE
        )

    def _score_sentence(self, sentence: str) -> float:
        """
        Score a sentence based on information value.
        Higher score = more valuable information.
        """
        score = 0.0

        # Check for high-value patterns
        matches = self.high_value_regex.findall(sentence)
        score += len(matches) * 2.0

        # Check for numbers (concrete data)
        numbers = re.findall(r'[\d,.]+\s*(?:%|rm|myr|usd|million|billion|m|b)?', sentence, re.IGNORECASE)
        score += len(numbers) * 1.0

        # Check for specific names/entities (proper nouns)
        capitals = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', sentence)
        score += len(capitals) * 0.3

        # Penalize very short or very long sentences
        word_count = len(sentence.split())
        if word_count < 5:
            score *= 0.5
        elif word_count > 50:
            score *= 0.7

        return score

    def _extract_key_sentences(
        self,
        text: str,
        max_sentences: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Extract the most informative sentences from text.

        Returns:
            List of (sentence, score) tuples, sorted by score descending
        """
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)

        # Score each sentence
        scored = [(s.strip(), self._score_sentence(s)) for s in sentences if len(s.strip()) > 20]

        # Sort by score (highest first)
        scored.sort(key=lambda x: x[1], reverse=True)

        return scored[:max_sentences]

    def _deduplicate_content(self, sentences: List[str], similarity_threshold: float = 0.7) -> List[str]:
        """
        Remove semantically similar sentences to avoid redundancy.
        Uses simple word overlap for efficiency (no embeddings).
        """
        if not sentences:
            return []

        unique = [sentences[0]]

        for sentence in sentences[1:]:
            words_new = set(sentence.lower().split())

            is_duplicate = False
            for existing in unique:
                words_existing = set(existing.lower().split())
                if not words_new or not words_existing:
                    continue

                # Calculate Jaccard similarity
                intersection = len(words_new & words_existing)
                union = len(words_new | words_existing)
                similarity = intersection / union if union > 0 else 0

                if similarity > similarity_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique.append(sentence)

        return unique

    def optimize_news_content(
        self,
        articles: List[Dict[str, Any]],
        max_chars: int = 3500,
        format_style: str = "bullet"
    ) -> str:
        """
        Optimize news articles for maximum information within char limit.

        Args:
            articles: List of article dicts with 'title', 'content', citation_id
            max_chars: Maximum characters for output
            format_style: "bullet" for bullet points, "prose" for paragraphs

        Returns:
            Optimized content string
        """
        all_insights = []

        for article in articles:
            citation_id = article.get('citation_id', '')
            title = article.get('title', '')
            content = article.get('content', '')

            # Extract key sentences from content
            key_sentences = self._extract_key_sentences(content, max_sentences=5)

            # Add title as high-priority insight
            all_insights.append({
                'text': title,
                'score': 10.0,  # Titles are always important
                'citation': citation_id,
                'type': 'title'
            })

            # Add key sentences
            for sentence, score in key_sentences:
                if score > 0.5:  # Only include sentences with some value
                    all_insights.append({
                        'text': sentence,
                        'score': score,
                        'citation': citation_id,
                        'type': 'insight'
                    })

        # Sort by score
        all_insights.sort(key=lambda x: x['score'], reverse=True)

        # Deduplicate
        seen_texts = []
        unique_insights = []
        for insight in all_insights:
            # Simple dedup check
            text_lower = insight['text'].lower()
            if not any(self._similar_text(text_lower, seen) for seen in seen_texts):
                unique_insights.append(insight)
                seen_texts.append(text_lower)

        # Build output within char limit
        output_lines = []
        current_chars = 0

        for insight in unique_insights:
            if format_style == "bullet":
                line = f"• {insight['text']} [{insight['citation']}]"
            else:
                line = f"{insight['text']} [{insight['citation']}]"

            line_chars = len(line) + 1  # +1 for newline

            if current_chars + line_chars > max_chars:
                break

            output_lines.append(line)
            current_chars += line_chars

        return "\n".join(output_lines)

    def _similar_text(self, text1: str, text2: str, threshold: float = 0.6) -> bool:
        """Check if two texts are similar using word overlap."""
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return False

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return (intersection / union) > threshold if union > 0 else False

    def optimize_for_judge(
        self,
        news_analysis: str,
        financial_analysis: str,
        claims_analysis: str,
        max_total_tokens: int = 4000  # Leave room for output
    ) -> Tuple[str, str, str]:
        """
        Optimize all three analyses for Judge Agent within token budget.

        Allocation strategy:
        - News: 25% (sentiment, scandals)
        - Financial: 30% (numbers-heavy)
        - Claims: 45% (ESG critical for decisions)

        Returns:
            Tuple of (optimized_news, optimized_financial, optimized_claims)
        """
        total_chars = tokens_to_chars(max_total_tokens)

        # Allocation
        news_budget = int(total_chars * 0.20)      # ~20%
        financial_budget = int(total_chars * 0.25) # ~25%
        claims_budget = int(total_chars * 0.55)    # ~55% (Prioritize ESG details)

        # Smart truncation with key sentence extraction
        news_opt = self._smart_truncate(news_analysis, news_budget)
        financial_opt = self._smart_truncate(financial_analysis, financial_budget)
        claims_opt = self._smart_truncate(claims_analysis, claims_budget)

        return news_opt, financial_opt, claims_opt

    def _smart_truncate(self, text: str, max_chars: int) -> str:
        """
        Smart truncation that preserves key information.
        """
        if len(text) <= max_chars:
            return text

        # Extract key sentences
        key_sentences = self._extract_key_sentences(text, max_sentences=20)

        # Build output preserving structure
        output = []
        current_chars = 0
        reserve = 50  # Reserve for "... [TRUNCATED]"

        # Try to keep section headers if present
        lines = text.split('\n')
        for line in lines:
            if line.startswith('#') or line.startswith('**'):  # Markdown headers
                if current_chars + len(line) < max_chars - reserve:
                    output.append(line)
                    current_chars += len(line) + 1

        # Add high-value sentences
        for sentence, score in key_sentences:
            if score < 1.0:
                continue

            if current_chars + len(sentence) + 10 < max_chars - reserve:
                # Check if already included
                if sentence not in '\n'.join(output):
                    output.append(sentence)
                    current_chars += len(sentence) + 1

        result = '\n'.join(output)

        if len(result) < len(text):
            result += "\n... [KEY INSIGHTS EXTRACTED]"

        return result

    def create_dense_summary_prompt(self, analysis_type: str) -> str:
        """
        Generate a prompt suffix that encourages dense, information-rich output.
        """
        return f"""
OUTPUT REQUIREMENTS:
1. Use BULLET POINTS (•) for all findings - no prose paragraphs
2. Each bullet MUST contain: specific metric/fact + citation
3. Format: "• [Metric]: [Value] [N#/F#/D#]"
4. NO generic statements like "company shows growth" - ONLY specific data
5. Maximum 8 bullets per section
6. Prioritize: Numbers > Dates > Named entities > General observations

EXAMPLE GOOD OUTPUT:
• Revenue: RM 15.2B (+12% YoY) [F1]
• Net profit margin: 23.5% (industry avg: 18%) [F1]
• CEO announced expansion to Vietnam Q2 2025 [N2]
• Net Zero 2050 commitment with SBTi validation [D3]

EXAMPLE BAD OUTPUT (DO NOT DO THIS):
The company has shown strong financial performance with good revenue growth...
"""


# Singleton instance
content_optimizer = ContentOptimizer()
