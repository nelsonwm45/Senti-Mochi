import apiClient from '../apiClient';

export interface CompanyOverview {
	id: string;
	name: string;
	ticker: string;
	sector?: string;
	market_cap?: number;
	summary?: string;
	recent_news: NewsItem[];
	recent_filings: FilingItem[];
	financial_ratios: RatioItem[];
}

export interface NewsItem {
	id: string;
	title: string;
	url: string;
	published_at: string;
	sentiment: string;
}

export interface FilingItem {
	id: string;
	type: string;
	date: string;
	summary: string;
}

export interface RatioItem {
	name: string;
	value: number;
	period: string;
}

export const companyApi = {
	getOverview: async (id: string): Promise<CompanyOverview> => {
		const response = await apiClient.get<CompanyOverview>(`/companies/${id}/overview`);
		return response.data;
	},
};
