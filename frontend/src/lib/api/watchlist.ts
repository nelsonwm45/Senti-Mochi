import apiClient from '../apiClient';

export interface WatchlistItem {
	id: string;
	company: {
		id: string;
		name: string;
		ticker: string;
		sector: string;
	};
}

export const watchlistApi = {
	getAll: async () => {
		const { data } = await apiClient.get<WatchlistItem[]>('/watchlist/');
		return data;
	},
	add: async (companyId: string) => {
		const { data } = await apiClient.post<WatchlistItem>('/watchlist/', { companyId });
		return data;
	},
	remove: async (id: string) => {
		await apiClient.delete(`/watchlist/${id}`);
	},
};
