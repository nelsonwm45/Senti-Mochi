import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, ArrowRightLeft, ChevronRight, ChevronDown, Trash2, Plus, Loader2, Pin, Clock } from 'lucide-react';
import { useWatchlistStore } from '@/store/watchlistStore';
import { GlassCard } from '@/components/ui/GlassCard';
import { GlassInput } from '@/components/ui/GlassInput'; 
import { SearchPopout } from './SearchPopout';
import { cn } from '@/lib/utils';
import { analysisApi, AnalysisReport } from '@/lib/api/analysis';

interface PinnedCompany {
  id: string;
  name: string;
  ticker: string;
}

interface CompanyAnalysisData {
  status: string | null;
  lastUpdated: string | null;
  loading: boolean;
}

interface WatchlistTableProps {
  onCompare: (selectedTickers: string[]) => void;
  onViewDetails: (ticker: string) => void;
  // Optional pin functionality (used in Dashboard)
  onPin?: (company: PinnedCompany) => void;
  isPinned?: (companyId: string) => boolean;
  maxPinned?: number;
  pinnedCount?: number;
}

// Helper to format date
const formatDate = (dateString: string | null): string => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) {
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    if (diffHours === 0) {
      const diffMins = Math.floor(diffMs / (1000 * 60));
      return diffMins <= 1 ? 'Just now' : `${diffMins}m ago`;
    }
    return `${diffHours}h ago`;
  } else if (diffDays === 1) {
    return 'Yesterday';
  } else if (diffDays < 7) {
    return `${diffDays}d ago`;
  } else {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }
};

// Helper to get status badge styling
const getStatusBadge = (status: string | null) => {
  if (!status) return { bg: 'bg-gray-500/10', text: 'text-gray-400', border: 'border-gray-500/20', label: 'No Analysis' };
  
  const upperStatus = status.toUpperCase();
  if (['ENGAGE', 'BUY', 'APPROVE', 'OVERWEIGHT'].includes(upperStatus)) {
    return { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20', label: status };
  }
  if (['AVOID', 'SELL', 'REJECT', 'UNDERWEIGHT'].includes(upperStatus)) {
    return { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/20', label: status };
  }
  // Monitor, Hold, etc.
  return { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/20', label: status };
};

export function WatchlistTable({ 
  onCompare, 
  onViewDetails,
  onPin,
  isPinned,
  maxPinned = 3,
  pinnedCount = 0
}: WatchlistTableProps) {
  const { watchlist, removeFromWatchlist, fetchWatchlist } = useWatchlistStore();
  const [searchQuery, setSearchQuery] = useState(''); // Local filter for existing items
  const [selectedForComparison, setSelectedForComparison] = useState<string[]>([]);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [analysisData, setAnalysisData] = useState<Record<string, CompanyAnalysisData>>({});
  const [sectorFilter, setSectorFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  useEffect(() => {
      fetchWatchlist();
  }, [fetchWatchlist]);

  // Fetch analysis data for all companies
  useEffect(() => {
    const fetchAnalysisData = async () => {
      for (const company of watchlist) {
        // Skip if already loaded
        if (analysisData[company.id] && !analysisData[company.id].loading) continue;
        
        // Mark as loading
        setAnalysisData(prev => ({
          ...prev,
          [company.id]: { status: null, lastUpdated: null, loading: true }
        }));

        try {
          const reports = await analysisApi.getReports(company.id);
          if (reports && reports.length > 0) {
            const latestReport = reports[0];
            setAnalysisData(prev => ({
              ...prev,
              [company.id]: {
                status: latestReport.rating,
                lastUpdated: latestReport.created_at,
                loading: false
              }
            }));
          } else {
            setAnalysisData(prev => ({
              ...prev,
              [company.id]: { status: null, lastUpdated: null, loading: false }
            }));
          }
        } catch (err) {
          console.warn(`Failed to fetch analysis for ${company.name}:`, err);
          setAnalysisData(prev => ({
            ...prev,
            [company.id]: { status: null, lastUpdated: null, loading: false }
          }));
        }
      }
    };

    if (watchlist.length > 0) {
      fetchAnalysisData();
    }
  }, [watchlist]);

  // Get unique sectors from watchlist
  const sectors = Array.from(new Set(watchlist.map(c => c.sector).filter(Boolean)));

  // Filter companies based on search, sector, and status
  const filteredWatchlist = watchlist.filter((c) => {
    // Search filter
    const matchesSearch = !searchQuery || 
      c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.ticker.toLowerCase().includes(searchQuery.toLowerCase());
    
    // Sector filter
    const matchesSector = sectorFilter === 'all' || c.sector === sectorFilter;
    
    // Status filter
    const analysis = analysisData[c.id];
    const companyStatus = analysis?.status?.toUpperCase() || null;
    let matchesStatus = statusFilter === 'all';
    if (statusFilter === 'engage') matchesStatus = companyStatus === 'ENGAGE';
    if (statusFilter === 'monitor') matchesStatus = companyStatus === 'MONITOR';
    if (statusFilter === 'avoid') matchesStatus = companyStatus === 'AVOID';
    if (statusFilter === 'not-analyzed') matchesStatus = !companyStatus;
    
    return matchesSearch && matchesSector && matchesStatus;
  });

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

      {/* Search and Filter Bar */}
      <div className="flex flex-col md:flex-row gap-3">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search by name or ticker..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all"
          />
        </div>

        {/* Sector Filter */}
        <div className="relative">
          <select
            value={sectorFilter}
            onChange={(e) => setSectorFilter(e.target.value)}
            className="appearance-none pl-4 pr-10 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white text-sm font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/50 hover:bg-white/10 transition-colors cursor-pointer min-w-[140px]"
          >
            <option value="all" className="bg-gray-900">All Sectors</option>
            {sectors.map((sector) => (
              <option key={sector} value={sector} className="bg-gray-900">
                {sector}
              </option>
            ))}
          </select>
          <ChevronDown size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
        </div>

        {/* Status Filter */}
        <div className="relative">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="appearance-none pl-4 pr-10 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white text-sm font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/50 hover:bg-white/10 transition-colors cursor-pointer min-w-[140px]"
          >
            <option value="all" className="bg-gray-900">All Status</option>
            <option value="engage" className="bg-gray-900">Engage</option>
            <option value="monitor" className="bg-gray-900">Monitor</option>
            <option value="avoid" className="bg-gray-900">Avoid</option>
            <option value="not-analyzed" className="bg-gray-900">Not Analyzed</option>
          </select>
          <ChevronDown size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
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
                <th className="p-6">Status</th>
                <th className="p-6">Last Updated</th>
                <th className="p-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filteredWatchlist.length === 0 ? (
                <tr>
                    <td colSpan={5} className="p-8 text-center text-gray-500">
                        No companies in watchlist. Search to add.
                    </td>
                </tr>
              ) : (
                filteredWatchlist.map((company) => {
                  const isSelected = selectedForComparison.includes(company.ticker);
                  const analysis = analysisData[company.id] || { status: null, lastUpdated: null, loading: true };
                  const statusBadge = getStatusBadge(analysis.status);
                  
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
                      <td className="p-6">
                        {analysis.loading ? (
                          <Loader2 size={16} className="animate-spin text-gray-400" />
                        ) : (
                          <div className={cn(
                            "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border",
                            statusBadge.bg, statusBadge.text, statusBadge.border
                          )}>
                            {statusBadge.label}
                          </div>
                        )}
                      </td>
                      <td className="p-6 text-gray-400 text-sm">
                        {analysis.loading ? (
                          <span className="text-gray-500">-</span>
                        ) : (
                          <div className="flex items-center gap-1.5">
                            <Clock size={14} className="text-gray-500" />
                            {formatDate(analysis.lastUpdated)}
                          </div>
                        )}
                      </td>
                      <td className="p-6">
                        <div className="flex justify-end gap-2">
                          {/* Pin Button (only shown if onPin is provided) */}
                          {onPin && (
                            <button
                              onClick={() => {
                                if (!isPinned?.(company.id)) {
                                  onPin({ id: company.id, name: company.name, ticker: company.ticker });
                                }
                              }}
                              disabled={isPinned?.(company.id) || pinnedCount >= maxPinned}
                              className={cn(
                                "p-2 rounded-lg border transition-all duration-200",
                                isPinned?.(company.id)
                                  ? 'bg-indigo-500 border-indigo-500 text-white shadow-[0_0_15px_rgba(99,102,241,0.5)]'
                                  : pinnedCount >= maxPinned
                                    ? 'bg-transparent border-white/5 text-gray-600 cursor-not-allowed'
                                    : 'bg-transparent border-white/10 text-gray-400 hover:text-indigo-400 hover:border-indigo-500/30'
                              )}
                              aria-label={isPinned?.(company.id) ? "Pinned" : "Pin to Dashboard"}
                              title={isPinned?.(company.id) ? "Already pinned" : pinnedCount >= maxPinned ? `Max ${maxPinned} pinned` : "Pin to Dashboard"}
                            >
                              <Pin size={18} />
                            </button>
                          )}

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
