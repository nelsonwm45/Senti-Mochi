"""
News Relevance Filter Service

Filters out irrelevant news articles before passing to AI agents.
Solves the "Malayan tiger" problem for "Maybank" searches.

Two-stage filtering:
1. Keyword-based quick filter (fast, no API calls)
2. Semantic similarity filter (uses existing embedding service)
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlmodel import Session
from app.models import NewsArticle, Company
import re


# Financial/business keywords that indicate relevance
BUSINESS_KEYWORDS = {
    # General business
    'revenue', 'profit', 'loss', 'earnings', 'dividend', 'stock', 'share',
    'quarter', 'annual', 'fiscal', 'financial', 'market', 'trading',
    'investor', 'investment', 'acquisition', 'merger', 'ipo', 'listing',
    'ceo', 'cfo', 'chairman', 'board', 'director', 'management',
    'analyst', 'rating', 'forecast', 'guidance', 'outlook',

    # Banking specific
    'bank', 'banking', 'loan', 'credit', 'deposit', 'interest', 'rate',
    'mortgage', 'financing', 'asset', 'liability', 'capital', 'reserve',
    'npl', 'non-performing', 'provision', 'impairment',

    # ESG
    'esg', 'sustainability', 'carbon', 'emission', 'climate', 'green',
    'governance', 'compliance', 'regulation', 'audit',

    # Malaysian specific
    'bursa', 'klse', 'ringgit', 'myr', 'bnm', 'securities commission',
    'sc malaysia', 'ftse', 'klci',
}

# Keywords that indicate NON-business content (negative filter)
NON_BUSINESS_KEYWORDS = {
    'tiger', 'wildlife', 'animal', 'zoo', 'conservation', 'species',
    'forest', 'jungle', 'habitat', 'extinct', 'poaching',
    'football', 'soccer', 'cricket', 'badminton', 'sports', 'match',
    'movie', 'film', 'actor', 'actress', 'entertainment', 'celebrity',
    'recipe', 'cooking', 'food review', 'restaurant review',
    'weather', 'typhoon', 'monsoon', 'flood warning',
}


class NewsRelevanceFilter:
    """
    Filters news articles for business relevance to a company.
    """

    def __init__(self, similarity_threshold: float = 0.65):
        """
        Args:
            similarity_threshold: Minimum cosine similarity for semantic filter (0-1)
        """
        self.similarity_threshold = similarity_threshold

    def _normalize_company_name(self, name: str) -> List[str]:
        """
        Generate variations of company name for matching.
        E.g., "Malayan Banking Berhad" -> ["malayan banking", "maybank", "malayan bank"]
        """
        name_lower = name.lower()
        variations = [name_lower]

        # Remove common suffixes
        for suffix in ['berhad', 'bhd', 'sdn', 'ltd', 'limited', 'inc', 'corp', 'corporation']:
            name_lower = name_lower.replace(suffix, '').strip()
        variations.append(name_lower)

        # Add common abbreviations/aliases
        name_aliases = {
            'malayan banking': ['maybank'],
            'public bank': ['pbbank', 'pbb'],
            'hong leong bank': ['hlb', 'hong leong'],
            'cimb': ['cimb bank', 'cimb group'],
            'rhb bank': ['rhb'],
            'ammb holdings': ['ambank', 'am bank'],
            'affin bank': ['affin'],
            'alliance bank': ['alliance'],
            'tenaga nasional': ['tnb', 'tenaga'],
            'petronas': ['petroliam nasional'],
            'top glove': ['topglove'],
            'press metal': ['press metal aluminium'],
            'sime darby': ['sime'],
        }

        for key, aliases in name_aliases.items():
            if key in name_lower:
                variations.extend(aliases)

        return list(set(variations))

    def _quick_keyword_filter(
        self,
        article: Dict[str, Any],
        company_variations: List[str]
    ) -> Tuple[bool, float, str]:
        """
        Stage 1: Fast keyword-based relevance check.

        Returns:
            (is_relevant, confidence_score, reason)
        """
        title = (article.get('title') or '').lower()
        content = (article.get('content') or '').lower()
        text = f"{title} {content}"

        # Check if company name appears
        company_mentioned = any(var in text for var in company_variations)

        if not company_mentioned:
            return False, 0.0, "Company not mentioned"

        # Check for non-business keywords (negative signal)
        non_business_count = sum(1 for kw in NON_BUSINESS_KEYWORDS if kw in text)
        if non_business_count >= 2:
            # High non-business signal - likely irrelevant
            return False, 0.2, f"Non-business content detected ({non_business_count} keywords)"

        # Check for business keywords (positive signal)
        business_count = sum(1 for kw in BUSINESS_KEYWORDS if kw in text)

        if business_count >= 3:
            return True, 0.9, f"Strong business relevance ({business_count} keywords)"
        elif business_count >= 1:
            return True, 0.7, f"Moderate business relevance ({business_count} keywords)"
        else:
            # Company mentioned but no business keywords - uncertain
            return True, 0.5, "Company mentioned, context unclear"

    def _semantic_filter(
        self,
        article: Dict[str, Any],
        company_name: str,
        company_sector: Optional[str] = None
    ) -> Tuple[bool, float, str]:
        """
        Stage 2: Semantic similarity check using embeddings.
        Only called when keyword filter is uncertain (confidence < 0.7).
        """
        try:
            from app.services.embedding_service import embedding_service

            # Build company context for embedding
            sector_context = f" in the {company_sector} sector" if company_sector else ""
            company_context = f"{company_name}{sector_context} financial news, business updates, stock market, corporate announcements"

            # Get article text
            article_text = f"{article.get('title', '')} {article.get('content', '')[:500]}"

            # Generate embeddings
            embeddings = embedding_service.generate_embeddings([company_context, article_text])

            if len(embeddings) < 2:
                return True, 0.5, "Embedding failed, allowing article"

            # Calculate cosine similarity
            import numpy as np
            vec1 = np.array(embeddings[0])
            vec2 = np.array(embeddings[1])

            similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

            if similarity >= self.similarity_threshold:
                return True, float(similarity), f"Semantic similarity: {similarity:.2f}"
            else:
                return False, float(similarity), f"Low semantic similarity: {similarity:.2f}"

        except Exception as e:
            print(f"[RELEVANCE] Semantic filter error: {e}")
            # On error, allow the article through
            return True, 0.5, f"Semantic filter error: {str(e)}"

    def filter_articles(
        self,
        articles: List[Dict[str, Any]],
        company_name: str,
        company_sector: Optional[str] = None,
        use_semantic: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Filter a list of articles for relevance to the company.

        Args:
            articles: List of article dictionaries
            company_name: Company name to filter for
            company_sector: Optional sector for better semantic matching
            use_semantic: Whether to use semantic filtering for uncertain cases

        Returns:
            Filtered list of relevant articles with relevance_score added
        """
        if not articles:
            return []

        company_variations = self._normalize_company_name(company_name)
        relevant_articles = []

        for article in articles:
            # Stage 1: Quick keyword filter
            is_relevant, confidence, reason = self._quick_keyword_filter(article, company_variations)

            # Stage 2: Semantic filter for uncertain cases
            if is_relevant and confidence < 0.7 and use_semantic:
                is_relevant, confidence, reason = self._semantic_filter(
                    article, company_name, company_sector
                )

            if is_relevant:
                article_with_score = article.copy()
                article_with_score['relevance_score'] = confidence
                article_with_score['relevance_reason'] = reason
                relevant_articles.append(article_with_score)
            else:
                print(f"[RELEVANCE] Filtered out: '{article.get('title', '')[:50]}...' - {reason}")

        # Sort by relevance score (highest first)
        relevant_articles.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

        print(f"[RELEVANCE] Kept {len(relevant_articles)}/{len(articles)} articles for {company_name}")

        return relevant_articles

    def filter_news_articles_db(
        self,
        session: Session,
        articles: List[NewsArticle],
        company: Company
    ) -> List[NewsArticle]:
        """
        Filter NewsArticle model instances (database objects).

        Args:
            session: Database session
            articles: List of NewsArticle instances
            company: Company instance

        Returns:
            Filtered list of relevant NewsArticle instances
        """
        # Convert to dict format for filtering
        article_dicts = [
            {
                'id': str(a.id),
                'title': a.title,
                'content': a.content,
                'url': a.url,
                'published_at': a.published_at,
                'source': a.source,
                '_db_article': a  # Keep reference to original
            }
            for a in articles
        ]

        filtered_dicts = self.filter_articles(
            article_dicts,
            company.name,
            company.sector
        )

        # Extract original NewsArticle instances
        return [d['_db_article'] for d in filtered_dicts]


# Singleton instance
news_relevance_filter = NewsRelevanceFilter()
