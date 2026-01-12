import apiClient from '../apiClient';

export interface NewsItem {
	id: string;
	title: string;
	source: string;
	url: string;
	published_at: string;
	sentiment: 'Positive' | 'Negative' | 'Neutral' | 'Adverse';
	summary?: string;
	content_preview?: string;
	company_ticker?: string;
}

export const newsApi = {
	getAll: async () => {
		const { data } = await apiClient.get<NewsItem[]>('/news/');
		return data;
	},
};
