'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, X, Plus, Loader2, Check } from 'lucide-react';
import { GlassInput } from '@/components/ui/GlassInput';
import { useWatchlistStore } from '@/store/watchlistStore';
import { companiesApi, Company } from '@/lib/api/companies';
// import { searchBursaCompanies, BursaCompany } from '@/lib/bursaCompanies'; // Legacy

interface SearchPopoutProps {
  isOpen: boolean;
  onClose: () => void;
  userId: string;
}

export function SearchPopout({ isOpen, onClose, userId }: SearchPopoutProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Company[]>([]);
  const [loading, setLoading] = useState(false);

  const [addingTicker, setAddingTicker] = useState<string | null>(null);
  const [addedTickers, setAddedTickers] = useState<Set<string>>(new Set());
  const { addToWatchlist } = useWatchlistStore();

  const [error, setError] = useState<string | null>(null);
  
  // Debounce search
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Initial fetch or search
    const fetchCompanies = async () => {
        setLoading(true);
        try {
            const data = await companiesApi.search(query);
            setResults(data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    if (!query) {
        // Immediate fetch for initial list
        fetchCompanies();
        return;
    }

    if (debounceRef.current) clearTimeout(debounceRef.current);

    debounceRef.current = setTimeout(fetchCompanies, 300);

    return () => {
        if (debounceRef.current) clearTimeout(debounceRef.current);
    }
  }, [query]);

  const handleAdd = async (company: { ticker: string, name?: string }) => {
    if (addingTicker || addedTickers.has(company.ticker)) return;
    
    setAddingTicker(company.ticker);
    setError(null);
    try {
        await addToWatchlist(company.ticker, userId);
        setAddedTickers(prev => new Set(prev).add(company.ticker));
    } catch (err) {
        console.error("Failed to add", err);
        setError(`Failed to add ${company.ticker}. Please try again.`);
    } finally {
        setAddingTicker(null);
    }
  };


  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          >
            {/* Modal */}
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-lg bg-slate-900/90 border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[80vh]"
            >
              <div className="p-6 border-b border-white/10">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-bold text-white">Add to Watchlist</h2>
                  <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
                    <X size={24} />
                  </button>
                </div>

                {error && (
                    <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 text-red-200 text-sm rounded-lg flex items-center gap-2">
                        <span>{error}</span>
                    </div>
                )}


                <div className="relative">
                  <GlassInput
                    autoFocus
                    leftIcon={loading ? <Loader2 size={20} className="animate-spin text-accent" /> : <Search size={20} />}
                    placeholder="Search Bursa Ticker or Name..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    className="w-full"
                  />
                </div>
              </div>
              
              <div className="flex-1 overflow-y-auto p-2">
                  {loading && results.length === 0 ? (
                      <div className="text-center py-12">
                          <Loader2 className="animate-spin text-accent mx-auto mb-3" size={32} />
                          <p className="text-gray-400">Loading companies...</p>
                      </div>
                  ) : results.length === 0 ? (
                      <div className="text-center py-8 text-gray-400">
                          <p className="mb-4">
                              {query ? "No companies found." : "No companies available yet."}
                          </p>
                          {query && !loading && (
                              <button
                                  onClick={() => handleAdd({ ticker: query.toUpperCase() })}
                                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-colors flex items-center gap-2 mx-auto"
                                  title="Add Custom Ticker"
                              >
                                  {addingTicker === query.toUpperCase() ? <Loader2 className="animate-spin" size={16} /> : <Plus size={16} />}
                                  <span>Add "{query.toUpperCase()}"</span>
                              </button>
                          )}
                      </div>
                  ) : (
                      <div className="space-y-1">
                          {query && !results.find(c => c.ticker === query.toUpperCase()) && !loading && (
                             /* Option to add exact query as fallback if not in list but user wants to try */
                              <div className="flex items-center justify-between p-3 hover:bg-white/5 rounded-xl group transition-colors border border-dashed border-white/20 mb-2">
                                  <div>
                                      <div className="font-bold text-white">{query.toUpperCase()}</div>
                                      <div className="text-sm text-gray-400">Global Search / Custom</div>
                                  </div>
                                  <button
                                      onClick={() => handleAdd({ ticker: query.toUpperCase() })}
                                      className="p-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg"
                                  >
                                      <Plus size={18} />
                                  </button>
                              </div>
                          )}
                          
                          {results.map(company => {
                              const isAdded = addedTickers.has(company.ticker);
                              const isAdding = addingTicker === company.ticker;
                              
                              return (
                                <div key={company.ticker} className="flex items-center justify-between p-3 hover:bg-white/5 rounded-xl group transition-colors">
                                    <div className="min-w-0 pr-4">
                                        <div className="font-bold text-white truncate">{company.ticker}</div>
                                        <div className="text-sm text-gray-400 truncate">{company.name}</div>
                                        <div className="text-xs text-gray-500">{company.sector}</div>
                                    </div>
                                    
                                    <button
                                        onClick={() => handleAdd(company)}
                                        disabled={isAdded || isAdding}
                                        className={`p-2 rounded-lg transition-all flex-shrink-0 ${
                                            isAdded 
                                            ? 'bg-green-500/20 text-green-400 cursor-default'
                                            : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg hover:shadow-indigo-500/25'
                                        }`}
                                    >
                                        {isAdding ? (
                                            <Loader2 size={18} className="animate-spin" />
                                        ) : isAdded ? (
                                            <Check size={18} />
                                        ) : (
                                            <Plus size={18} />
                                        )}
                                    </button>
                                </div>
                              );
                          })}
                      </div>
                  )}
              </div>
              
              <div className="p-4 bg-black/20 text-center text-xs text-gray-500 border-t border-white/5">
                {loading ? 'Searching...' : `Showing ${results.length} result(s).`}
              </div>
            </motion.div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
