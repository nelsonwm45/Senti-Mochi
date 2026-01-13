import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Company, mockCompanies } from '@/lib/mockData';

interface WatchlistState {
	watchlist: Company[];
	addToWatchlist: (ticker: string) => void;
	removeFromWatchlist: (ticker: string) => void;
	isInWatchlist: (ticker: string) => boolean;
}

export const useWatchlistStore = create<WatchlistState>()(
	persist(
		(set, get) => ({
			watchlist: [mockCompanies[0], mockCompanies[1]], // Initial seeded data
			addToWatchlist: (ticker) => {
				const company = mockCompanies.find((c) => c.ticker === ticker);
				if (company && !get().watchlist.find((c) => c.ticker === ticker)) {
					set((state) => ({ watchlist: [...state.watchlist, company] }));
				}
			},
			removeFromWatchlist: (ticker) => {
				set((state) => ({
					watchlist: state.watchlist.filter((c) => c.ticker !== ticker),
				}));
			},
			isInWatchlist: (ticker) => {
				return !!get().watchlist.find((c) => c.ticker === ticker);
			},
		}),
		{
			name: 'watchlist-storage',
		}
	)
);
