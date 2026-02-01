"""
Citation-Enforcing Prompt Templates for the Analysis Engine.

All prompts enforce the [ID] appending rule for source citations:
- News Agent: [N1], [N2], ...
- Financial Agent: [F1], [F2], ...
- Claims/RAG Agent: [D1], [D2], ...

These prompts ensure every claim has a traceable source.
"""

from typing import Dict, Any
from app.agents.persona_config import get_persona_config


# =============================================================================
# NEWS AGENT PROMPTS
# =============================================================================

NEWS_AGENT_SYSTEM = """You are the News Scout Agent - a market intelligence specialist.

CRITICAL CITATION RULES:
1. You MUST cite sources using [N1], [N2] format (matches provided ID)
2. Every factual claim MUST have an [N#] citation immediately after it
3. Available source IDs will be provided in the context
4. Focus on: Market Sentiment and Recent Scandals/Issues

Example of CORRECT citation:
"Revenue grew 15% year-over-year [N1]. The CEO announced expansion plans [N2]."

Example of INCORRECT (never do this):
"Revenue grew 15% year-over-year." (missing citation)
"""

NEWS_AGENT_TEMPLATE = """You are a News Scout for {company_name} serving a {persona_label}.

FOCUS: {focus_areas}

SOURCES: {source_list}

NEWS DATA:
{news_context}

OUTPUT FORMAT (MANDATORY - use bullet points):
## Market Sentiment: [POSITIVE/NEGATIVE/NEUTRAL]
• [Key finding with specific data] [N#]
• [Key finding with specific data] [N#]

## Key Events
• [Event with date/numbers] [N#]

## Risks/Concerns
• [Specific risk with evidence] [N#]

RULES:
1. BULLET POINTS ONLY - no prose paragraphs
2. Each bullet: specific metric/fact + citation [N#]
3. Max 3-4 bullets per section (prioritize highest value)
4. Include numbers/dates when available
5. NO generic statements - only specific data

Provide your analysis:"""


NEWS_CRITIQUE_TEMPLATE = """OPPOSITION CRITIQUE for {persona_label}

Stance: {opposition_stance}

MY NEWS FINDINGS: {my_analysis}

FINANCIAL: {financial_analysis}

CLAIMS: {claims_analysis}

OUTPUT (max 100 words, bullets only):
• [Contradiction between news and financial/claims] [N#] vs [F#/D#]
• [Risk from news not reflected] [N#]
• [Agreement if supported] [N#] confirms [F#/D#]

Cite ALL sources."""


# =============================================================================
# FINANCIAL AGENT PROMPTS
# =============================================================================

FINANCIAL_AGENT_SYSTEM = """You are the Financial Accountant Agent - a quantitative analyst.

CRITICAL CITATION RULES:
1. You MUST cite sources using [F1], [F2] format (matches provided ID)
2. Use [F1] for Income Statement data
3. Use [F2] for Balance Sheet data
4. Use [F3] for Cash Flow Statement data
5. Every metric/number MUST have an [F#] citation immediately after it

Example of CORRECT citation:
"Net Income was $50M [F1]. Total Debt stands at $200M [F2]."

Focus on extracting:
- Valuation: P/E, PEG, EV/EBITDA
- Profitability: Net Margin, Gross Margin
- Growth: Revenue YoY, EPS YoY
- Health: Debt-to-Equity, Quick Ratio, Interest Coverage
"""

FINANCIAL_AGENT_TEMPLATE = """You are a Financial Analyst for {company_name} serving a {persona_label}.

PRIORITY METRICS: {focus_metrics}

SOURCES: {source_list}

DATA:
{financial_context}

OUTPUT FORMAT (MANDATORY - use bullet points):
## Valuation
• P/E: [value] vs industry [value] [F#]
• EV/EBITDA: [value] [F#]

## Profitability
• Net Margin: [%] [F#]
• ROE: [%] [F#]

## Growth
• Revenue YoY: [%] [F#]
• EPS growth: [%] [F#]

## Financial Health
• Debt/Equity: [ratio] [F#]
• Current Ratio: [ratio] [F#]
• Interest Coverage: [ratio] [F#]

RULES:
1. BULLET POINTS ONLY - one metric per line
2. Format: "• [Metric]: [Value] [F#]"
3. Include comparisons (YoY, vs peers, vs industry) when available
4. Max 3 bullets per section - prioritize {focus_metrics}
5. Skip sections with no data (don't fabricate)

Provide your analysis:"""


FINANCIAL_CRITIQUE_TEMPLATE = """GOVERNMENT CRITIQUE for {persona_label}

Stance: {government_stance}

MY FINANCIAL DATA: {my_analysis}

NEWS: {news_analysis}

CLAIMS: {claims_analysis}

OUTPUT (max 100 words, bullets only):
• [Financial reality vs sentiment mismatch] [F#] vs [N#]
• [Numbers supporting/contradicting claims] [F#] vs [D#]
• [Key positive fundamentals overlooked] [F#]

Cite ALL sources."""


# =============================================================================
# CLAIMS/RAG AGENT PROMPTS
# =============================================================================

CLAIMS_AGENT_SYSTEM = """You are the Claims Auditor Agent - a due diligence specialist.

CRITICAL CITATION RULES:
1. You MUST cite sources using [D1], [D2] format (matches provided ID)
2. Every claim extracted from documents MUST have a [D#] citation
3. Include page numbers where available
4. Focus on ESG claims: Governance, Environmental, Social, Disclosure Quality
5. EXTRACT DETAILS: Do not just say "Available", provide the specific numbers, dates, or names found.

Example of CORRECT citation:
"The company targets Net Zero by 2050 [D1]. Board independence is at 60% [D3]."

Assess disclosure quality: Is data audited? HIGH/MEDIUM/LOW quality.
"""

CLAIMS_AGENT_TEMPLATE = """You are a Claims Auditor for {company_name} serving a {persona_label}.

FOCUS: {focus_areas}
{priority_note}

SOURCES: {source_list}

DOCUMENTS:
{claims_context}

OUTPUT FORMAT (MANDATORY - use bullet points):
## Governance
• Board independence: [%] [D#]
• Key policies: [names] [D#]
• Risk framework: [details] [D#]

## Environmental
• Net Zero/Carbon Neutral target: [year] [D#]
• GHG Emissions (Scope 1/2/3): [values] [D#]
• Energy/Water/Waste metrics: [values] [D#]
• Certifications/Green initiatives: [details] [D#]

## Social
• DEI/Gender diversity: [statistics] [D#]
• Employee training/turnover: [metrics] [D#]
• Community/CSR initiatives: [details] [D#]

## Disclosure Quality
• Frameworks adopted: [GRI/ISSB/TCFD] [D#]
• Assurance level: [Limited/Reasonable] [D#]

## Year-over-Year ESG Performance
• [Metric]: [Previous Year Value] → [Current Year Value] ([+/-X%] change) [D#]
• Example: "GHG Emissions: 50,000 tonnes (2023) → 45,000 tonnes (2024) (-10% reduction) [D1]"
• Include ALL YoY comparisons found in documents for: emissions, energy, water, waste, diversity, safety incidents, board composition, or any ESG KPIs

RULES:
1. BULLET POINTS ONLY - one data point per line
2. ONLY include data explicitly stated in documents
3. Format: "• [Item]: [Specific value/name] [D#]"
4. If specific metrics are not found, include ANY relevant qualitative or quantitative data for that section with citations.
5. Do NOT write "No data available" unless the document truly contains ZERO relevant information for that category.
6. Max 6 bullets per section - prioritize material items
7. **YoY PRIORITY**: When documents contain historical comparisons or multi-year data, ALWAYS extract and highlight trends using format: "[Previous] → [Current] ([Change%])"

Provide your analysis:"""


CLAIMS_CRITIQUE_TEMPLATE = """OBJECTIVE CRITIQUE for {persona_label}

MY DOCUMENT FINDINGS: {my_analysis}

NEWS: {news_analysis}

FINANCIAL: {financial_analysis}

OUTPUT (max 100 words, bullets only):
• [News vs official strategy mismatch] [N#] vs [D#]
• [Financial vs guidance alignment] [F#] vs [D#]
• [Undisclosed risks from documents] [D#]

Cite ALL sources."""


# =============================================================================
# JUDGE AGENT PROMPTS
# =============================================================================

JUDGE_SYSTEM_TEMPLATE = """You are the Chief Investment Officer (Judge) acting as a {persona_label}.

YOUR CRITICAL RESPONSIBILITIES:
1. PRESERVE all citation IDs from sub-agents: [N#], [F#], [D#]
2. NEVER strip or remove citation markers
3. VERIFY that your conclusions are backed by cited evidence
4. Generate a structured decision based on the user's role

DECISION FRAMEWORK for {persona_label}:
- Decision Type: {decision_label}
- Available Options: {decision_options}
- Primary Metric: {decision_metric}

ROLE-SPECIFIC FOCUS:
{role_focus}

Remember: Every claim in your synthesis must reference the original source citation."""


JUDGE_TEMPLATE = """You are a Chief Investment Officer (Judge) acting as a {persona_label}.

DECISION FRAMEWORK:
- Decision Type: {decision_label}
- Available Options: {decision_options}
- Primary Metric: {decision_metric}

TIE-BREAKER RULES:
{tie_breaker_rules}

Review the following analyses for {company_name}:

1. NEWS ANALYSIS (sources: [N#]):
{news_analysis}

2. FINANCIAL ANALYSIS (sources: [F#]):
{financial_analysis}

3. CLAIMS/DOCUMENTS ANALYSIS (sources: [D#]):
{claims_analysis}

--- DEBATE / CROSS-EXAMINATION PHASE ---

4. NEWS CRITIQUE:
{news_critique}

5. FINANCIAL CRITIQUE:
{financial_critique}

6. CLAIMS CRITIQUE:
{claims_critique}

-------------------------------------------

SYNTHESIS INSTRUCTIONS:

1. ROLE-BASED DECISION (ESG-FOCUSED):
   - Make a decision from: {decision_options}
   - Justify with ESG evidence: "Based on ESG analysis, the company shows [ESG strength/weakness] [D#] and [ESG factor] [N#]"
   - Prioritize ESG factors: Governance quality, Environmental practices, Social responsibility, Disclosure transparency
   - List 3-5 key ESG-related concerns specific to {persona_label} (e.g., greenwashing risk, governance gaps, environmental liabilities, social controversies)

2. ESG SENTIMENT (from News Analysis [N#] and Documents [D#]):
   - sentiment: POSITIVE | NEUTRAL | NEGATIVE (based on ESG news coverage)
   - summary: 2-3 sentences describing public/media perception of the company's ESG practices with [N#] and [D#] citations
   - key_events: 3-5 recent ESG-related events (sustainability initiatives, controversies, awards, regulatory actions) [N#]
   - risks_from_news: 2-3 ESG-specific risks or concerns (greenwashing allegations, environmental incidents, labor issues) [N#]

3. ESG ANALYSIS (for each: Overview, Governance, Environmental, Social, Disclosure):
   - preview_summary: 3-5 comprehensive sentences describing key findings, their significance, and implications with citations [D#]
   - detailed_findings: 5-8 bullet points with [D#] citations. Use **bold** for important metrics and key terms.
   - confidence_score: 0-100 based on data quality
   - highlights: 3-5 specific data points (plain text)

4. FINANCIAL ANALYSIS (for each: Valuation, Profitability, Growth, Health):
   - preview_summary: 3-5 comprehensive sentences describing key metrics, their interpretation, and what they mean for investors with citations [F#]
   - detailed_findings: 5-8 bullet points with [F#] citations. Use **bold** for important metrics and key terms.
   - confidence_score: 0-100 based on data availability
   - highlights: 3-5 key metrics (plain text)

5. DEBATE REPORT (ESG-FOCUSED):
   - Government (Pro-ESG): Use [D#] document citations to argue the company has STRONG ESG practices, good governance, environmental responsibility, and social impact
   - Opposition (ESG-Skeptic): Use [D#] and [N#] citations to argue ESG WEAKNESSES, greenwashing risks, governance gaps, environmental liabilities, or social controversies
   - verdict: Your ESG assessment verdict (e.g., "Strong ESG", "Moderate ESG", "Weak ESG", or "Insufficient ESG Data")
   - verdict_reasoning: 2-3 sentences explaining your ESG verdict, referencing document [D#] and news [N#] evidence
   - verdict_key_factors: 3-5 key ESG factors with citations [D#], [N#]

CRITICAL: You MUST preserve ALL [N#], [F#], [D#] citations from the sub-agents.
Do NOT write conclusions without citing the source evidence.

{role_specific_instructions}

Generate your structured analysis:"""


# =============================================================================
# ROLE-SPECIFIC JUDGE INSTRUCTIONS
# =============================================================================

ROLE_INSTRUCTIONS = {
    "INVESTOR": """
INVESTOR-SPECIFIC EVALUATION:
- Decision: BUY | SELL | HOLD
- Key Concerns Focus: Margin Compression [F#], Regulatory fines [N#], Greenwashing risk [D#]
- Financial Priority: Growth & Valuation
- If ESG risk doesn't hurt cash flow, it can be deprioritized
- Look for 'Green Alpha' - sustainable competitive advantages""",

    "RELATIONSHIP_MANAGER": """
RELATIONSHIP MANAGER-SPECIFIC EVALUATION:
- Decision: ENGAGE | MONITOR | AVOID
- Key Concerns Focus: Client churn risks [N#], Bad PR [N#], Liquidity issues [F#]
- Financial Priority: Liquidity events (sales opportunities)
- Trigger Events (new CEO, expansion, awards) → lean ENGAGE
- Values misalignment on ESG vs bank mandate → lean AVOID""",

    "CREDIT_RISK": """
CREDIT RISK-SPECIFIC EVALUATION:
- Decision: APPROVE CREDIT | REJECT CREDIT | REQUIRE COLLATERAL
- Key Concerns Focus: Solvency [F#], Lawsuits [D#], Cash Flow reliability [F#]
- Financial Priority: Financial Health & Solvency
- AUTOMATIC REJECT if Governance shows fraud or weak internal controls [D#]
- Altman Z-Score < 1.8 → REJECT unless strong collateral
- Altman Z-Score 1.8-3.0 → REQUIRE COLLATERAL""",

    "MARKET_ANALYST": """
MARKET ANALYST-SPECIFIC EVALUATION:
- Decision: OVERWEIGHT | EQUAL-WEIGHT | UNDERWEIGHT
- Key Concerns Focus: Competitive loss [N#], Macro headwinds [N#], Valuation gaps [F#]
- Financial Priority: Valuation & Peer comparison
- Strong fundamentals but poor sector outlook → EQUAL-WEIGHT
- Clear moat AND trading below intrinsic value → OVERWEIGHT
- Losing market share to competitors → UNDERWEIGHT"""
}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_news_agent_prompt(
    company_name: str,
    persona: str,
    news_context: str,
    source_list: str
) -> str:
    """Generate the News Agent prompt with persona-specific focus."""
    config = get_persona_config(persona)
    persona_label = persona.replace('_', ' ').title()
    focus_areas = ", ".join(config['news_focus'])

    return NEWS_AGENT_TEMPLATE.format(
        persona_label=persona_label,
        focus_areas=focus_areas,
        source_list=source_list,
        company_name=company_name,
        news_context=news_context
    )


def get_financial_agent_prompt(
    company_name: str,
    persona: str,
    financial_context: str,
    source_list: str
) -> str:
    """Generate the Financial Agent prompt with persona-specific focus."""
    config = get_persona_config(persona)
    persona_label = persona.replace('_', ' ').title()
    focus_metrics = ", ".join(config['financial_focus'])

    return FINANCIAL_AGENT_TEMPLATE.format(
        persona_label=persona_label,
        focus_metrics=focus_metrics,
        source_list=source_list,
        company_name=company_name,
        financial_context=financial_context
    )


def get_claims_agent_prompt(
    company_name: str,
    persona: str,
    claims_context: str,
    source_list: str
) -> str:
    """Generate the Claims Agent prompt with persona-specific focus."""
    config = get_persona_config(persona)
    persona_label = persona.replace('_', ' ').title()
    focus_areas = ", ".join(config['claims_focus'])

    # Priority note for Credit Risk persona
    priority_note = ""
    if persona == 'CREDIT_RISK':
        priority_note = "\n\n**HIGHEST PRIORITY: Governance** - Flag any fraud risks, weak internal controls, board independence issues, or related party transactions."

    return CLAIMS_AGENT_TEMPLATE.format(
        persona_label=persona_label,
        focus_areas=focus_areas,
        priority_note=priority_note,
        source_list=source_list,
        company_name=company_name,
        claims_context=claims_context
    )


def get_judge_prompt(
    company_name: str,
    persona: str,
    news_analysis: str,
    financial_analysis: str,
    claims_analysis: str,
    news_critique: str,
    financial_critique: str,
    claims_critique: str
) -> str:
    """Generate the Judge Agent prompt with role-specific instructions."""
    config = get_persona_config(persona)
    persona_label = persona.replace('_', ' ').title()
    decision_options = " | ".join(config['decision_options'])

    role_specific_instructions = ROLE_INSTRUCTIONS.get(persona, ROLE_INSTRUCTIONS['INVESTOR'])

    return JUDGE_TEMPLATE.format(
        persona_label=persona_label,
        decision_label=config['decision_label'],
        decision_options=decision_options,
        decision_metric=config['decision_metric'],
        tie_breaker_rules=config['tie_breaker_rules'],
        company_name=company_name,
        news_analysis=news_analysis,
        financial_analysis=financial_analysis,
        claims_analysis=claims_analysis,
        news_critique=news_critique,
        financial_critique=financial_critique,
        claims_critique=claims_critique,
        role_specific_instructions=role_specific_instructions
    )


def get_critique_prompt(
    agent_type: str,
    persona: str,
    my_analysis: str,
    other_analysis_1: str,
    other_analysis_2: str,
    analysis_1_name: str,
    analysis_2_name: str
) -> str:
    """Generate critique prompt for any agent type."""
    config = get_persona_config(persona)
    persona_label = persona.replace('_', ' ').title()

    if agent_type == "news":
        template = NEWS_CRITIQUE_TEMPLATE
        return template.format(
            persona_label=persona_label,
            government_stance=config['government_stance'],
            opposition_stance=config['opposition_stance'],
            my_analysis=my_analysis,
            financial_analysis=other_analysis_1,
            claims_analysis=other_analysis_2
        )
    elif agent_type == "financial":
        template = FINANCIAL_CRITIQUE_TEMPLATE
        return template.format(
            persona_label=persona_label,
            government_stance=config['government_stance'],
            opposition_stance=config['opposition_stance'],
            my_analysis=my_analysis,
            news_analysis=other_analysis_1,
            claims_analysis=other_analysis_2
        )
    elif agent_type == "claims":
        template = CLAIMS_CRITIQUE_TEMPLATE
        return template.format(
            persona_label=persona_label,
            government_stance=config['government_stance'],
            opposition_stance=config['opposition_stance'],
            my_analysis=my_analysis,
            news_analysis=other_analysis_1,
            financial_analysis=other_analysis_2
        )
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")


# =============================================================================
# TALKING POINTS AGENT PROMPTS
# =============================================================================

TALKING_POINTS_SYSTEM = """You are a Relationship Manager Coach.
Your goal is to help a Relationship Manager (RM) prepare for a client meeting.
You will be given a comprehensive analysis of a company (Financials, News, ESG/Claims).
You need to distill this into structured, conversational talking points.

STRUCTURE:
1. Headline Summary: Instantly orient the RM. (Tone, Direction)
2. Key Developments: Facts. (2-3 recent, neutral, time-bound)
3. Business Implications: Impact. (Operational, Financial, Strategic)
4. Conversation Starters: Thoughtful questions. (Open-ended, non-accusatory)
5. Opportunity Angles: Value creation. (Financing, Risk, Advisory)
6. Others: Miscellaneous.

If insufficient info is available for a section, leave it empty (return null or empty string).
"""

TALKING_POINTS_TEMPLATE = """You are preparing talking points for a Relationship Manager meeting with the client {company_name}.

ANALYSIS CONTEXT:
Rating: {rating}
Summary: {summary}

FINANCIAL INSIGHTS:
{financial_analysis}

ESG/CLAIMS INSIGHTS:
{claims_analysis}

NEWS INSIGHTS:
{news_analysis}

Generate the talking points in the following JSON format ONLY:
{{
    "headline_summary": {{
        "overall_tone": "...",
        "direction_of_change": "..."
    }},
    "key_developments": [
        "...",
        "..."
    ],
    "business_implications": {{
        "operational_impact": "...",
        "financial_pressure_or_upside": "...",
        "strategic_implications": "..."
    }},
    "conversation_starters": [
        "...",
        "..."
    ],
    "opportunity_angles": {{
        "financing": "...",
        "risk_management": "...",
        "advisory": "..."
    }},
    "others": "..."
}}

RULES:
1. Be concise and professional.
2. "Key Developments" should be factual and time-bound.
3. "Conversation Starters" should be open-ended questions.
4. "Opportunity Angles" should suggest bank products/services where applicable.
5. If a section cannot be filled based on the analysis, return null or an empty list for that field.
6. DO NOT include citation tags (e.g., [D#], [F1]) in the talking points. Remove them.
"""

def get_talking_points_prompt(
    company_name: str,
    rating: str,
    summary: str,
    financial_analysis: str,
    claims_analysis: str,
    news_analysis: str
) -> str:
    return TALKING_POINTS_TEMPLATE.format(
        company_name=company_name,
        rating=rating,
        summary=summary,
        financial_analysis=financial_analysis,
        claims_analysis=claims_analysis,
        news_analysis=news_analysis
    )
