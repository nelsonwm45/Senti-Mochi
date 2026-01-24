import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, ArrowRightLeft, ChevronRight, Trash2, Plus, Loader2 } from 'lucide-react';
import { useWatchlistStore } from '@/store/watchlistStore';
import { GlassCard } from '@/components/ui/GlassCard';
import { GlassInput } from '@/components/ui/GlassInput'; 
import { SearchPopout } from './SearchPopout';

// Temporary helper to parse JWT


interface WatchlistTableProps {
  onCompare: (selectedTickers: string[]) => void;
  onViewDetails: (ticker: string) => void;
}

export function WatchlistTable({ onCompare, onViewDetails }: WatchlistTableProps) {
  const { watchlist, removeFromWatchlist, fetchWatchlist } = useWatchlistStore();
  const [searchQuery, setSearchQuery] = useState(''); // Local filter for existing items
  const [selectedForComparison, setSelectedForComparison] = useState<string[]>([]);
  const [isSearchOpen, setIsSearchOpen] = useState(false);


  useEffect(() => {
      fetchWatchlist();
  }, [fetchWatchlist]);

  // Filter companies based on local search of the watchlist
  const filteredWatchlist = watchlist.filter(
    (c) =>
      c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.ticker.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleToggleComparison = (ticker: string) => {
    if (selectedForComparison.includes(ticker)) {
      setSelectedForComparison(prev => prev.filter(t => t !== ticker));
    } else {
      if (selectedForComparison.length < 2) {
        setSelectedForComparison(prev => [...prev, ticker]);
      } else {
         setSelectedForComparison(prev => [...prev, ticker].slice(-2));
      }
    }
  };

  const handleRemove = (ticker: string) => {
      removeFromWatchlist(ticker);
      setSelectedForComparison(prev => prev.filter(t => t !== ticker));
  };

  return (
    <div className="space-y-6">
      {/* Header & Search */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Active Watchlist</h1>
          <p className="text-gray-400">Manage core coverage and risk monitoring assets.</p>
        </div>
        <div className="w-full md:w-auto relative z-20">
            <button
                onClick={() => setIsSearchOpen(true)}
                className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl transition-colors font-medium whitespace-nowrap"
            >
                <Plus size={18} />
                <span>Add</span>
            </button>
        </div>
      </div>
      
      <SearchPopout isOpen={isSearchOpen} onClose={() => setIsSearchOpen(false)} />

      {/* Table */}
      <GlassCard className="p-0 overflow-hidden">
        <div className="w-full overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/5 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                <th className="p-6">Company</th>
                <th className="p-6">Sector</th>
                <th className="p-6">Market Cap</th>
                <th className="p-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filteredWatchlist.length === 0 ? (
                <tr>
                    <td colSpan={4} className="p-8 text-center text-gray-500">
                        No companies in watchlist. Search to add.
                    </td>
                </tr>
              ) : (
                filteredWatchlist.map((company) => {
                  const isSelected = selectedForComparison.includes(company.ticker);
                  return (
                    <tr key={company.ticker} className="group hover:bg-white/[0.02] transition-colors">
                      <td className="p-6">
                        <div className="font-bold text-white mb-1">{company.ticker}</div>
                        <div className="text-sm text-gray-400">{company.name}</div>
                      </td>
                      <td className="p-6 text-gray-300">
                        <div className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
                          {company.sector}
                        </div>
                      </td>
                      <td className="p-6 text-gray-300 font-mono">{company.marketCap}</td>
                      <td className="p-6">
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => handleToggleComparison(company.ticker)}
                            className={`p-2 rounded-lg border transition-all duration-200 ${
                              isSelected
                                ? 'bg-indigo-500 border-indigo-500 text-white shadow-[0_0_15px_rgba(99,102,241,0.5)]'
                                : 'bg-transparent border-white/10 text-gray-400 hover:text-white hover:border-white/30'
                            }`}
                            aria-label="Compare"
                          >
                            <ArrowRightLeft size={18} />
                          </button>
                          
                          <button
                            onClick={() => onViewDetails(company.ticker)}
                            className="p-2 rounded-lg border border-white/10 text-gray-400 hover:text-white hover:border-white/30 bg-transparent transition-all duration-200"
                            aria-label="View Details"
                          >
                            <ChevronRight size={18} />
                          </button>
                          
                          <button
                            onClick={() => handleRemove(company.ticker)}
                            className="p-2 rounded-lg border border-white/10 text-gray-400 hover:text-red-400 hover:border-red-500/30 hover:bg-red-500/10 transition-all duration-200"
                            aria-label="Remove"
                          >
                            <Trash2 size={18} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </GlassCard>

      {/* Comparison Tray */}
      <AnimatePresence>
        {selectedForComparison.length > 0 && (
          <motion.div
            initial={{ y: 100, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 100, opacity: 0 }}
            className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40"
          >
             <div className="bg-[#6366f1] text-white px-6 py-3 rounded-2xl shadow-2xl flex items-center gap-6 border border-indigo-400/30">
                <div className="flex items-center gap-3 font-semibold">
                    <ArrowRightLeft size={20} />
                    Comparison Tray
                </div>
                
                <div className="flex gap-2">
                    {selectedForComparison.map(ticker => (
                        <span key={ticker} className="px-3 py-1 bg-white/20 rounded-lg text-sm font-bold backdrop-blur-sm">
                            {ticker}
                        </span>
                    ))}
                    {selectedForComparison.length < 2 && (
                         <span className="px-3 py-1 text-sm text-indigo-200 italic">
                            Select 1 more
                        </span>
                    )}
                </div>

                <div className="h-6 w-px bg-white/20"></div>

                <button 
                    disabled={selectedForComparison.length < 2}
                    onClick={() => onCompare(selectedForComparison)}
                    className="bg-white text-indigo-600 px-4 py-1.5 rounded-lg text-sm font-bold shadow-sm hover:bg-indigo-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    Compare Assets
                </button>
                 <button 
                    onClick={() => setSelectedForComparison([])}
                    className="text-white/70 hover:text-white transition-colors"
                >
                    ×
                </button>
             </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
