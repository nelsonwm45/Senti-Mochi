export type AnalysisPersona = 'INVESTOR' | 'RELATIONSHIP_MANAGER' | 'CREDIT_RISK' | 'MARKET_ANALYST';

export interface PersonaConfig {
    id: AnalysisPersona;
    label: string;
    description: string;
    icon: string; // Icon name from lucide-react
    focusAreas: string[];
    decisionType: string;
    color: {
        primary: string;
        secondary: string;
        accent: string;
    };
    metrics: string[];
    chartTypes: string[];
}

export const PERSONA_CONFIGS: Record<AnalysisPersona, PersonaConfig> = {
    INVESTOR: {
        id: 'INVESTOR',
        label: 'Investment Dashboard',
        description: 'Focus on financial performance, growth metrics, and investment returns',
        icon: 'TrendingUp',
        focusAreas: ['Revenue Growth', 'Profitability', 'Return on Equity', 'Market Trends'],
        decisionType: 'Investment Decision',
        color: {
            primary: 'emerald',
            secondary: 'emerald',
            accent: 'emerald'
        },
        metrics: ['Revenue Growth', 'EPS', 'ROE'],
        chartTypes: ['line', 'bar', 'area']
    },
    RELATIONSHIP_MANAGER: {
        id: 'RELATIONSHIP_MANAGER',
        label: 'Client Relationship Dashboard',
        description: 'Track client engagement, quarterly performance, and sentiment',
        icon: 'Users',
        focusAreas: ['Client Engagement', 'Quarterly Results', 'Sentiment Analysis', 'Opportunity Pipeline'],
        decisionType: 'Client Relationship Decision',
        color: {
            primary: 'blue',
            secondary: 'blue',
            accent: 'blue'
        },
        metrics: ['Engagement Opportunities', 'Quarterly Results', 'Client Sentiment'],
        chartTypes: ['line', 'bar', 'gauge']
    },
    CREDIT_RISK: {
        id: 'CREDIT_RISK',
        label: 'Credit Risk Dashboard',
        description: 'Monitor credit risk, debt ratios, and warning indicators',
        icon: 'ShieldCheck',
        focusAreas: ['Risk Assessment', 'Debt Metrics', 'Financial Stability', 'Warning Signals'],
        decisionType: 'Credit Risk Decision',
        color: {
            primary: 'red',
            secondary: 'orange',
            accent: 'red'
        },
        metrics: ['Risk Score', 'Debt/Equity', 'Red Flags'],
        chartTypes: ['bar', 'gauge', 'scatter']
    },
    MARKET_ANALYST: {
        id: 'MARKET_ANALYST',
        label: 'Market Analysis Dashboard',
        description: 'Analyze market position, valuation, and competitive landscape',
        icon: 'BarChart3',
        focusAreas: ['Market Position', 'Valuation Metrics', 'Market Share', 'Competitive Analysis'],
        decisionType: 'Market Analysis Decision',
        color: {
            primary: 'amber',
            secondary: 'amber',
            accent: 'amber'
        },
        metrics: ['Market Position', 'Valuation', 'Market Share'],
        chartTypes: ['bar', 'line', 'area']
    }
};
