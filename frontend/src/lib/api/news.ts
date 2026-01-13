import apiClient from '../apiClient';

export interface SentimentData {
	label: 'Positive' | 'Neutral' | 'Negative';
	score: number;
	confidence: number;
	analyzed_at?: string;
}

export interface UnifiedFeedItem {
	id: string;
	companyId: string;  // Company UUID for filtering
	type: 'bursa' | 'star' | 'nst';
	title: string;
	link: string;
	date: string; // ISO string
	timestamp: number;
	company: string;
	companyCode: string;
	description?: string;
	source: string;
	sentiment?: SentimentData;
}

export const newsApi = {
	/**
	 * Get unified news feed
	 */
	async getFeed(limit: number = 50, watchlistOnly: boolean = true): Promise<UnifiedFeedItem[]> {
		const { data } = await apiClient.get<UnifiedFeedItem[]>('/api/v1/news/feed', {
			params: { limit, watchlist_only: watchlistOnly },
		});
		return data;
	}
};
