"""
Persona Configuration Module for Polymorphic Analysis

This module centralizes all persona-specific directives for the Company Analysis Engine.
Each persona changes retrieval strategies, debate focus, and final verdicts.
"""

from typing import Dict, List, TypedDict


class PersonaDirectives(TypedDict):
    """Configuration structure for each analysis persona."""
    # Agent Focus Areas
    financial_focus: List[str]
    news_focus: List[str]
    claims_focus: List[str]

    # Semantic Search Queries
    financial_query: str
    news_query: str
    claims_queries: Dict[str, str]  # E, S, G, Disclosure

    # Debate Stances for Cross-Examination
    government_stance: str  # Pro-company/investment stance
    opposition_stance: str  # Skeptic stance

    # Decision Configuration
    decision_options: List[str]
    decision_label: str
    decision_metric: str
    tie_breaker_rules: str


PERSONA_CONFIG: Dict[str, PersonaDirectives] = {
    # =========================================================================
    # INVESTOR PERSONA - Growth & Return Focused
    # =========================================================================
    "INVESTOR": {
        "financial_focus": [
            "Revenue Growth (YoY)",
            "EPS Trends",
            "Profit Margin Expansion",
            "ROE (Return on Equity)",
            "ROIC (Return on Invested Capital)",
            "Dividend Payout Ratio"
        ],
        "news_focus": [
            "M&A Rumors",
            "Product Launches",
            "Market Sentiment (hyped vs. beaten down)",
            "Analyst Upgrades/Downgrades"
        ],
        "claims_focus": [
            "Materiality (do ESG risks hurt profits?)",
            "Green Alpha (competitive moats like proprietary tech)"
        ],
        "financial_query": "Revenue growth YoY, EPS earnings per share trend, profit margin expansion, ROE return on equity, ROIC return on invested capital, dividend payout ratio, earnings quality",
        "news_query": "M&A rumors, product launches, market sentiment hype, analyst rating upgrade downgrade, expansion growth plans",
        "claims_queries": {
            "environmental": "Net Zero 2050, 2030 Decarbonisation Targets, sector pathways Thermal Coal Cement Palm Oil Power Oil & Gas Real Estate. Scope 1 2 3 GHG emissions, Financed Emissions, Carbon Intensity, Internal Carbon Pricing ICP. NDPE No Deforestation No Peat No Exploitation, Biodiversity Nature Statement, Nature-related risks, High Conservation Value HCV. Sustainable Finance GSSIPS, Sustainability-linked financing SLF, Transition finance, Green Bonds Sukuk. Physical risk, Transition risk, Climate Scenario Analysis, Climate Stress Testing. NZBA, TFF, SBTi, PCAF, TNFD, RECs.",
            "social": "Human Rights Due Diligence, Grievance Mechanism, Modern Slavery, Labor Standards. Women in leadership, Gender pay gap, Diversity Equity Inclusion DEI. Economic Inclusion, Financial Literacy, Underserved communities, B40, SME empowerment. Customer Experience CX, Net Promoter Score NPS, Data Privacy, Cybersecurity, Anti-scam Fraud prevention. Employee volunteerism, Occupational Health and Safety OHS, Talent retention, Sustainability culture. Humanising Financial Services, Targeted Relief and Recovery Facility, MSMEs empowerment, VBI.",
            "governance": "Board Oversight, Group Sustainability Governance Committee GSGC, Group Sustainability Council, Three Lines of Defence. Sustainability-linked KPIs, Remuneration linkage, Executive compensation. EWRM Enterprise-Wide Risk Management, Sustainability Risk Management Framework, Climate Risk Management Standard, Sustainability Watchlist. Anti-Bribery Corruption, Whistleblowing Policy, Tax Management, Vendor Code of Conduct VCOC. Shariah Governance for ESG.",
            "disclosure": "GRI Standards 2021, ISSB IFRS S1 S2, TCFD alignment, National Sustainability Reporting Framework NSRF. Double Materiality, Material Matters, Stakeholder Engagement. Limited Assurance, Independent Third-Party Verification, Data Reliability, ISAE 3000. Greenwashing risk mitigation, Science-based targets, Data completeness. SASB Standards, Data coverage ratios, Scope 3 data quality."
        },
        "government_stance": "Argue that the company is a Growth Machine. Highlight rising ROIC, new product success, and 'Green Alpha' moats that create sustainable competitive advantages.",
        "opposition_stance": "Argue that the stock is a Value Trap. Highlight slowing EPS, margin compression, or 'fluffy' ESG claims with no measurable profit impact.",
        "decision_options": ["BUY", "SELL", "HOLD"],
        "decision_label": "Investment Rating",
        "decision_metric": "Risk-Adjusted Return",
        "tie_breaker_rules": """
- If Financials are good but ESG is bad, look at "Materiality" - if the ESG risk doesn't hurt cash flow, it can be deprioritized.
- If confidence < 60 AND P/E > sector average: HOLD
- If dividend yield > 3% AND stable payout history: Lean BUY
- If revenue declining but margins expanding: HOLD for monitoring
"""
    },

    # =========================================================================
    # RELATIONSHIP MANAGER PERSONA - Client & Sales Focused
    # =========================================================================
    "RELATIONSHIP_MANAGER": {
        "financial_focus": [
            "Liquidity Events (recent cash raises/divestitures)",
            "Capex Plans (big spending upcoming)",
            "Working Capital Trends",
            "Revenue Stability"
        ],
        "news_focus": [
            "Trigger Events (New CEO/CFO, office expansion, awards)",
            "Crisis Management issues",
            "Partnership Announcements",
            "Geographic Expansion"
        ],
        "claims_focus": [
            "Values Alignment (e.g., Net Zero goals matching bank products)",
            "CSR Initiatives (co-sponsorship opportunities)"
        ],
        "financial_query": "Liquidity position, cash raise, divestiture, capex capital expenditure investment, working capital trends, revenue stability predictability, banking relationships",
        "news_query": "New CEO CFO executive appointment, office expansion, awards recognition, crisis management, partnership deal, strategic initiative",
        "claims_queries": {
            "environmental": "Sustainable Finance GSSIPS, Sustainability-linked financing SLF, Transition finance, Green Bonds Sukuk. Net Zero commitment, renewable energy targets, Green Energy Tariff GET, RECs. Transition Finance Framework TFF, Sectoral Decarbonisation Pathways.",
            "social": "Financial Inclusion, Economic Inclusion, Underserved communities, B40, SME empowerment, Micro Small Medium Enterprises MSMEs. Customer Experience CX, NPS. Employee volunteerism, Sustainability culture. Humanising Financial Services, VBI Values-based Intermediation.",
            "governance": "Client data protection, Cybersecurity, Anti-scam Fraud prevention. Ethical business practices, Anti-Bribery Corruption, Vendor Code of Conduct VCOC. Shariah Governance.",
            "disclosure": "Client communication quality, transparency, stakeholder engagement, integrated reporting. Assurance Reliability ISAE 3000."
        },
        "government_stance": "Argue that the client is Thriving & Needs Support. Highlight new awards, expansion plans, and alignment with our Green Bonds and sustainable finance products.",
        "opposition_stance": "Argue that the client is Stressed & Hidden Risk. Highlight leadership churn (New CEO), bad PR needing damage control, or lack of liquidity suggesting financial distress.",
        "decision_options": ["ENGAGE", "MONITOR", "AVOID"],
        "decision_label": "Relationship Potential",
        "decision_metric": "Client Lifetime Value",
        "tie_breaker_rules": """
- If "Trigger Events" (News) are present (new CEO, expansion, awards), output "ENGAGE" even if Financials are mediocre.
- If liquidity concerns BUT strong brand reputation: MONITOR
- If recent negative press BUT financial stability: MONITOR with enhanced due diligence
- If values misalignment on ESG (e.g., fossil fuel heavy vs our green mandate): AVOID unless clear remediation path
"""
    },

    # =========================================================================
    # CREDIT RISK PERSONA - Safety & Downside Focused
    # =========================================================================
    "CREDIT_RISK": {
        "financial_focus": [
            "Debt-to-Equity Ratio",
            "Current Ratio",
            "Interest Coverage Ratio",
            "Operating Cash Flow Consistency",
            "Altman Z-Score (Bankruptcy prediction)"
        ],
        "news_focus": [
            "Litigation & Fines",
            "Regulatory Headwinds (bans/tariffs)",
            "Credit Rating Changes",
            "Default Rumors"
        ],
        "claims_focus": [
            "Transition Risk (business model viability)",
            "Governance (fraud, board independence, internal controls) - HIGHEST PRIORITY"
        ],
        "financial_query": "Debt to equity ratio, current ratio, interest coverage, operating cash flow consistency, Altman Z-score bankruptcy prediction, leverage, default probability, quick ratio",
        "news_query": "Litigation lawsuit fine penalty, regulatory action ban tariff, credit rating downgrade, default bankruptcy rumors, covenant breach",
        "claims_queries": {
            "environmental": "Climate Risk, Physical risk, Transition risk, Climate Scenario Analysis, Climate Stress Testing. Stranded Assets, Carbon liabilities, Internal Carbon Pricing ICP. Financed Emissions PCAF, Scope 3 GHG. NGFS Scenarios Orderly Disorderly Hot House World.",
            "social": "Labor disputes, Modern Slavery, Human Rights Due Diligence. Supply chain disruption risk, NDPE. Occupational Health and Safety OHS. Data Privacy, Cybersecurity risks.",
            "governance": "Board Oversight, Three Lines of Defence, Group Sustainability Governance Committee. EWRM Enterprise-Wide Risk Management, Sustainability Risk Management Framework. Anti-Bribery Corruption, Whistleblowing Policy, Tax Management. Management integrity.",
            "disclosure": "Assurance Reliability ISAE 3000, Data Reliability, Greenwashing risk. Contingent liability disclosure, risk factor transparency. TCFD alignment, ISSB IFRS S1 S2."
        },
        "government_stance": "Argue that the company is a Fortress. Highlight strong Interest Coverage Ratio, consistent Operating Cash Flow, and clean Governance with independent board oversight.",
        "opposition_stance": "Argue that the company is a Default Risk. Highlight low Altman Z-Scores (distress zone < 1.8), pending lawsuits, and regulatory threats to their core business model.",
        "decision_options": ["APPROVE CREDIT", "REJECT CREDIT", "REQUIRE COLLATERAL"],
        "decision_label": "Credit Decision",
        "decision_metric": "Probability of Default (PD)",
        "tie_breaker_rules": """
- If "Governance" (ESG) shows fraud, weak internal controls, or board independence issues: AUTOMATIC REJECT regardless of Financials.
- If Altman Z-Score < 1.8 (Distress Zone): REJECT CREDIT unless strong collateral is provided.
- If Altman Z-Score between 1.8-3.0 (Grey Zone): REQUIRE COLLATERAL
- If Interest Coverage Ratio < 2x BUT improving trend: REQUIRE COLLATERAL
- If pending major litigation with material exposure: REQUIRE COLLATERAL or REJECT
"""
    },

    # =========================================================================
    # MARKET ANALYST PERSONA - The Big Picture
    # =========================================================================
    "MARKET_ANALYST": {
        "financial_focus": [
            "DCF Inputs (WACC, Terminal Growth)",
            "P/E vs Historical & Peers",
            "Quality of Earnings",
            "Revenue Mix by Segment"
        ],
        "news_focus": [
            "Macro Factors (Interest rate sensitivity, FX exposure)",
            "Supply Chain Dynamics",
            "Sector Rotation Trends",
            "Regulatory Changes"
        ],
        "claims_focus": [
            "Market Share Trends",
            "Peer Comparison (Margins vs. Competitors)"
        ],
        "financial_query": "DCF discounted cash flow valuation, WACC, terminal growth, P/E ratio, historical P/E, quality of earnings, revenue mix by segment",
        "news_query": "Macro factors interest rate sensitivity, FX exposure, supply chain dynamics, sector rotation, regulatory changes",
        "claims_queries": {
            "environmental": "Sector-specific pathways Thermal Coal Cement Palm Oil Power Oil & Gas. Net Zero Banking Alliance NZBA, SBTi targets. Green Alpha, Carbon Intensity vs peers. Transition Finance Framework TFF.",
            "social": "Diversity Equity Inclusion DEI comparison. Talent retention, Future-Fit Talent. Financial Inclusion impact B40 SME. Customer Welfare NPS comparison.",
            "governance": "Remuneration linkage, Sustainability-linked KPIs for executives. Board composition diversity. Anti-Bribery Corruption standards.",
            "disclosure": "GRI Standards 2021, ISSB IFRS S1 S2, TCFD, NSRF. Double Materiality assessment. Data coverage ratios, Scope 3 data quality. Independent Third-Party Verification."
        },
        "government_stance": "Argue that the company is a Sector Leader. Highlight pricing power, market share gains, and resilience to macro headwinds like interest rate changes.",
        "opposition_stance": "Argue that the company is Losing Relevance. Highlight superior competitors taking share, forex exposure risks, and weak 'Quality of Earnings' with one-time items.",
        "decision_options": ["OVERWEIGHT", "EQUAL-WEIGHT", "UNDERWEIGHT"],
        "decision_label": "Portfolio Weight",
        "decision_metric": "Relative Valuation",
        "tie_breaker_rules": """
- If "Macro Sensitivity" is high (e.g., high debt in high-interest environment): Downgrade rating.
- If P/E below sector average but growth slowing: EQUAL-WEIGHT
- If strong fundamentals but poor sector outlook: EQUAL-WEIGHT
- If clear competitive moat AND trading below intrinsic value: OVERWEIGHT
- If losing market share to competitors despite strong financials: UNDERWEIGHT
"""
    }
}


def get_persona_config(persona: str) -> PersonaDirectives:
    """
    Get configuration for a specific persona.

    Args:
        persona: The persona identifier (INVESTOR, RELATIONSHIP_MANAGER, CREDIT_RISK, MARKET_ANALYST)

    Returns:
        PersonaDirectives configuration dict. Defaults to INVESTOR if unknown persona.
    """
    return PERSONA_CONFIG.get(persona, PERSONA_CONFIG["INVESTOR"])


def get_all_personas() -> List[str]:
    """Return list of all available persona identifiers."""
    return list(PERSONA_CONFIG.keys())


def get_persona_display_info() -> Dict[str, Dict[str, str]]:
    """
    Get display information for all personas (for frontend use).

    Returns:
        Dict mapping persona ID to display info (label, description, decision_type)
    """
    return {
        "INVESTOR": {
            "label": "Investor",
            "description": "Growth & Return Focus",
            "decision_type": "BUY | SELL | HOLD",
            "icon": "TrendingUp"
        },
        "RELATIONSHIP_MANAGER": {
            "label": "Relationship Manager",
            "description": "Client & Sales Focus",
            "decision_type": "ENGAGE | MONITOR | AVOID",
            "icon": "Users"
        },
        "CREDIT_RISK": {
            "label": "Credit Risk",
            "description": "Safety & Downside Focus",
            "decision_type": "APPROVE | REJECT | COLLATERAL",
            "icon": "ShieldCheck"
        },
        "MARKET_ANALYST": {
            "label": "Market Analyst",
            "description": "Big Picture Focus",
            "decision_type": "OVER | EQUAL | UNDERWEIGHT",
            "icon": "BarChart3"
        }
    }
