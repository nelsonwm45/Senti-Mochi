
import apiClient from '../apiClient';

// =============================================================================
// CITATION-FIRST ANALYSIS ENGINE - TypeScript Types
// Matches the backend FinalAnalysisOutput structure
// =============================================================================

// Source metadata for citations
export interface SourceMetadata {
	id: string;           // Citation ID e.g., 'N1', 'F1', 'D1'
	title: string;        // Title of the source
	url_or_path: string;  // URL for news, file path for documents
	type: 'News' | 'Financial' | 'Document';
	date?: string;        // Publication date or period
	page_number?: number; // Page number for document sources
	row_line?: string;    // Specific row/line reference
}

// Section content structure (used by ESG and Financial reports)
export interface SectionContent {
	preview_summary: string;      // 1-2 sentence summary for collapsed view
	detailed_findings: string[];  // Bullet points with embedded citations
	confidence_score: number;     // 0-100 score
	highlights: string[];         // 3-5 key metrics
}

// Role-Based Insight (Decision Card at top)
export interface RoleBasedInsight {
	user_role: string;      // INVESTOR, RELATIONSHIP_MANAGER, CREDIT_RISK, MARKET_ANALYST
	decision: string;       // BUY/SELL/HOLD, ENGAGE/MONITOR/AVOID, etc.
	justification: string;  // Why this decision, with citations
	key_concerns: string[]; // Top concerns with citations
	confidence_score: number;
}

// ESG Report structure
export interface ESGReport {
	overview: SectionContent;
	governance_integration: SectionContent;
	environmental: SectionContent;
	social: SectionContent;
	disclosure_quality: SectionContent;
}

// Financial Report structure
export interface FinancialReport {
	valuation: SectionContent;
	profitability: SectionContent;
	growth: SectionContent;
	financial_health: SectionContent;
}

// Debate stance (Government/Opposition)
export interface DebateStance {
	stance_summary: string;
	arguments: string[];
}

// Debate Report structure
export interface DebateReport {
	government_stand: DebateStance;
	opposition_stand: DebateStance;
	judge_verdict: string;
	// Optional enhanced verdict fields
	verdict_reasoning?: string;
	verdict_key_factors?: string[];
}

// Market Sentiment structure (from News)
export interface MarketSentiment {
	sentiment: string;     // POSITIVE, NEUTRAL, NEGATIVE
	summary: string;       // 2-3 sentences with [N#] citations
	key_events: string[];  // Recent events with [N#] citations
	risks_from_news: string[]; // Risks with [N#] citations
}

// Agent log entry
export interface AgentLogEntry {
	agent: string;
	output: any;
}

// Main Analysis Report (matches backend AnalysisReport model)
export interface AnalysisReport {
	id: string;
	company_id: string;

	// Legacy top-level fields
	rating: string;  // BUY, SELL, HOLD, or role-specific
	confidence_score: number;
	summary: string;
	bull_case: string;
	bear_case: string;
	risk_factors: string;

	// Role-Based Insights (new Citation-First fields)
	justification?: string;    // Why this decision, with citations
	key_concerns?: string[];   // Top concerns with citations

	// New Citation-First structure
	esg_analysis: ESGReport;
	financial_analysis: FinancialReport;
	market_sentiment?: MarketSentiment;

	// Role-specific fields
	analysis_persona?: string;
	analysis_focus_area?: Record<string, any>;

	// Agent logs contain debate report and citation registry
	agent_logs?: AgentLogEntry[];

	created_at: string;
}

// Helper to extract debate report from agent_logs
export function getDebateReport(report: AnalysisReport): DebateReport | null {
	if (!report.agent_logs) return null;

	const debateLog = report.agent_logs.find(log => log.agent === 'debate');
	if (!debateLog) return null;

	return debateLog.output as DebateReport;
}

// Helper to extract citation registry from agent_logs
export function getCitationRegistry(report: AnalysisReport): Record<string, SourceMetadata> {
	if (!report.agent_logs) return {};

	const citationLog = report.agent_logs.find(log => log.agent === 'citation_registry');
	if (!citationLog) return {};

	return citationLog.output as Record<string, SourceMetadata>;
}

// Helper to build role-based insight from report data
export function getRoleBasedInsight(report: AnalysisReport): RoleBasedInsight {
	// Use actual key_concerns field if available, otherwise parse from risk_factors
	let keyConcerns = report.key_concerns || [];

	// Fallback: parse from risk_factors if key_concerns is empty
	if (keyConcerns.length === 0 && report.risk_factors) {
		keyConcerns = report.risk_factors
			.split('\n')
			.filter(line => line.trim().startsWith('-') || line.trim().startsWith('•'))
			.map(line => line.replace(/^[-•]\s*/, '').trim())
			.slice(0, 5);
	}


	return {
		user_role: report.analysis_persona || 'INVESTOR',
		decision: report.rating,
		justification: report.justification || report.summary,  // Use justification if available
		key_concerns: keyConcerns,
		confidence_score: report.confidence_score
	};
}

// Helper to extract Market Sentiment from agent_logs
export function getMarketSentiment(report: AnalysisReport): MarketSentiment | null {
	// First check top-level field (future proofing)
	if (report.market_sentiment && report.market_sentiment.sentiment) {
		return report.market_sentiment;
	}

	if (!report.agent_logs) return null;

	const sentimentLog = report.agent_logs.find(log => log.agent === 'market_sentiment');
	if (!sentimentLog) return null;

	return sentimentLog.output as MarketSentiment;
}

// =============================================================================
// API Status Types
// =============================================================================

export type AnalysisJobStatus =
	| 'PENDING'
	| 'GATHERING_INTEL'
	| 'CROSS_EXAMINATION'
	| 'SYNTHESIZING'
	| 'EMBEDDING'
	| 'COMPLETED'
	| 'FAILED'
	| 'no_analysis';

export interface AnalysisJobStatusResponse {
	job_id?: string;
	status: AnalysisJobStatus;
	current_step?: string;
	progress?: number;
	error_message?: string;
	started_at?: string;
	completed_at?: string;
	report_id?: string;
	message?: string;
}

// =============================================================================
// API Client
// =============================================================================

export const analysisApi = {
	triggerAnalysis: async (companyId: string, topic?: string, companyName?: string) => {
		const params = new URLSearchParams();
		if (topic) params.append('topic', topic);
		if (companyName) params.append('company_name', companyName);
		const queryString = params.toString();
		const url = queryString ? `/api/v1/analysis/${companyId}?${queryString}` : `/api/v1/analysis/${companyId}`;
		return apiClient.post(url);
	},

	getStatus: async (companyId: string): Promise<AnalysisJobStatusResponse> => {
		return apiClient.get(`/api/v1/analysis/${companyId}/status`).then(res => res.data);
	},

	getReports: async (companyId: string): Promise<AnalysisReport[]> => {
		return apiClient.get(`/api/v1/analysis/${companyId}/reports`).then(res => res.data);
	},

	getReport: async (reportId: string): Promise<AnalysisReport> => {
		return apiClient.get(`/api/v1/analysis/report/${reportId}`).then(res => res.data);
	},

	deleteReport: async (reportId: string): Promise<void> => {
		return apiClient.delete(`/api/v1/analysis/report/${reportId}`);
	}
};
