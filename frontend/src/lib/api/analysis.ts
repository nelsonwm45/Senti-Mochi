
import apiClient from '../apiClient';

export interface AnalysisReport {
	id: string;
	company_id: string;
	rating: 'BUY' | 'SELL' | 'HOLD';
	confidence_score: number;
	summary: string;
	bull_case: string;
	bear_case: string;
	risk_factors: string;
	esg_analysis: ESGAnalysisOutput;
	financial_analysis: FinancialAnalysisOutput;
	created_at: string;
	agent_logs?: any[];
}

export interface ESGTopic {
	score: number;
	summary: string;
	citations: string[];
	sources: string[];
}

export interface ESGAnalysisOutput {
	overview: ESGTopic;
	governance: ESGTopic;
	environmental: ESGTopic;
	social: ESGTopic;
	disclosure: ESGTopic;
}

export interface FinancialTopic {
	score: number;
	summary: string;
	citations: string[];
	sources: string[];
}

export interface FinancialAnalysisOutput {
	valuation: FinancialTopic;
	profitability: FinancialTopic;
	growth: FinancialTopic;
	health: FinancialTopic;
}

export const analysisApi = {
	triggerAnalysis: async (companyId: string) => {
		return apiClient.post(`/api/v1/analysis/${companyId}`);
	},

	getReports: async (companyId: string): Promise<AnalysisReport[]> => {
		return apiClient.get(`/api/v1/analysis/${companyId}/reports`).then(res => res.data);
	},

	getReport: async (reportId: string): Promise<AnalysisReport> => {
		return apiClient.get(`/api/v1/analysis/report/${reportId}`).then(res => res.data);
	}
};
