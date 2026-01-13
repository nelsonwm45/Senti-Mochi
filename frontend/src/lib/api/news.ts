import apiClient from '../apiClient';

export interface UnifiedFeedItem {
	id: string;
	type: 'bursa' | 'star' | 'nst';
	title: string;
	link: string;
	date: string; // ISO string
	timestamp: number;
	company: string;
	companyCode: string;
	description?: string;
	source: string;
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
