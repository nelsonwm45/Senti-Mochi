import { create } from 'zustand';
import apiClient from '@/lib/apiClient';
import { Company } from '@/lib/mockData'; // Keeping Interface, but will mockData usage will be removed from logic

interface WatchlistState {
	watchlist: Company[];
	isLoading: boolean;
	error: string | null;
	fetchWatchlist: () => Promise<void>;
	addToWatchlist: (ticker: string) => Promise<void>;
	removeFromWatchlist: (ticker: string) => Promise<void>;
	isInWatchlist: (ticker: string) => boolean;
}

export const useWatchlistStore = create<WatchlistState>((set, get) => ({
	watchlist: [],
	isLoading: false,
	error: null,

	fetchWatchlist: async () => {
		set({ isLoading: true, error: null });
		try {
			const response = await apiClient.get(`/api/v1/watchlist`);
			if (!response.data) throw new Error('Failed to fetch watchlist');
			set({ watchlist: response.data });
		} catch (error) {
			set({ error: (error as Error).message });
		} finally {
			set({ isLoading: false });
		}
	},

	addToWatchlist: async (ticker: string) => {
		set({ isLoading: true, error: null });
		try {
			const response = await apiClient.post(`/api/v1/watchlist?ticker=${ticker}`);
			if (!response.data) throw new Error('Failed to add to watchlist');

			// Refresh list to get full company details
			await get().fetchWatchlist();
		} catch (error) {
			set({ error: (error as Error).message });
			throw error; // Rethrow so components can show feedback
		} finally {
			set({ isLoading: false });
		}
	},

	removeFromWatchlist: async (ticker: string) => {
		set({ isLoading: true, error: null });
		try {
			const response = await apiClient.delete(`/api/v1/watchlist/${ticker}`);
			if (!response.data) throw new Error('Failed to remove from watchlist');

			set((state) => ({
				watchlist: state.watchlist.filter((c) => c.ticker !== ticker),
			}));
		} catch (error) {
			set({ error: (error as Error).message });
			throw error;
		} finally {
			set({ isLoading: false });
		}
	},

	isInWatchlist: (ticker) => {
		return !!get().watchlist.find((c) => c.ticker === ticker);
	},
}));
