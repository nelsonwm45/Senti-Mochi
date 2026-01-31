'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ProtectedLayout from '@/components/layouts/ProtectedLayout';
import usePersona from '@/hooks/usePersona';
import { TrendingUp, Shield, Users, BarChart3, Pin } from 'lucide-react';
import { GlassCard } from '@/components/ui/GlassCard';
import { WatchlistTable } from '@/app/watchlist/components/WatchlistTable';
import { ComparisonView } from '@/app/watchlist/components/ComparisonView';
import { CompanyDetails } from '@/app/watchlist/components/CompanyDetails';
import { PinnedCompanyCard } from './components/PinnedCompanyCard';
import { useWatchlistStore } from '@/store/watchlistStore';

type ViewState = 'list' | 'comparison' | 'details';

// Persona-specific headers
const personaHeaders: Record<string, { icon: any; title: string; subtitle: string; color: string }> = {
  INVESTOR: {
    icon: TrendingUp,
    title: 'Investment Dashboard',
    subtitle: 'Track your portfolio and analyze company performance',
    color: 'emerald'
  },
  RELATIONSHIP_MANAGER: {
    icon: Users,
    title: 'Client Dashboard',
    subtitle: 'Manage client relationships and track investment opportunities',
    color: 'blue'
  },
  CREDIT_RISK: {
    icon: Shield,
    title: 'Risk Dashboard',
    subtitle: 'Monitor credit risk and company financial health',
    color: 'amber'
  },
  MARKET_ANALYST: {
    icon: BarChart3,
    title: 'Analysis Dashboard',
    subtitle: 'Deep market analysis and company intelligence',
    color: 'purple'
  }
};

const PINNED_STORAGE_KEY = 'dashboard_pinned_companies';
const MAX_PINNED = 3;

interface PinnedCompany {
  id: string;
  name: string;
  ticker: string;
}

function DashboardContent() {
  const { persona, isLoading: personaLoading } = usePersona();
  const { watchlist } = useWatchlistStore();
  const [view, setView] = useState<ViewState>('list');
  const [comparisonTickers, setComparisonTickers] = useState<string[]>([]);
  const [detailTicker, setDetailTicker] = useState<string | null>(null);
  const [pinnedCompanies, setPinnedCompanies] = useState<PinnedCompany[]>([]);

  // Load pinned companies from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(PINNED_STORAGE_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        setPinnedCompanies(parsed);
      } catch (e) {
        console.error('Failed to parse pinned companies:', e);
      }
    }
  }, []);

  // Save pinned companies to localStorage when changed
  useEffect(() => {
    localStorage.setItem(PINNED_STORAGE_KEY, JSON.stringify(pinnedCompanies));
  }, [pinnedCompanies]);

  const handlePinCompany = (company: PinnedCompany) => {
    if (pinnedCompanies.length >= MAX_PINNED) {
      return; // Already at max
    }
    if (pinnedCompanies.find(p => p.id === company.id)) {
      return; // Already pinned
    }
    setPinnedCompanies(prev => [...prev, company]);
  };

  const handleUnpinCompany = (companyId: string) => {
    setPinnedCompanies(prev => prev.filter(p => p.id !== companyId));
  };

  const isPinned = (companyId: string) => {
    return pinnedCompanies.some(p => p.id === companyId);
  };

  const handleCompare = (tickers: string[]) => {
    setComparisonTickers(tickers);
    setView('comparison');
  };

  const handleViewDetails = (ticker: string) => {
    setDetailTicker(ticker);
    setView('details');
  };

  const handleBack = () => {
    setView('list');
    setComparisonTickers([]);
    setDetailTicker(null);
  };

  // Get persona-specific header
  const currentPersona = persona || 'INVESTOR';
  const header = personaHeaders[currentPersona] || personaHeaders.INVESTOR;
  const HeaderIcon = header.icon;
  const colorClasses = {
    emerald: 'bg-emerald-500/10 text-emerald-500',
    blue: 'bg-blue-500/10 text-blue-500',
    amber: 'bg-amber-500/10 text-amber-500',
    purple: 'bg-purple-500/10 text-purple-500'
  };
  const iconClass = colorClasses[header.color as keyof typeof colorClasses] || colorClasses.emerald;

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div className="flex items-center gap-3 mb-2">
          <div className={`p-2 rounded-xl ${iconClass}`}>
            <HeaderIcon size={24} />
          </div>
          <h1 className="text-3xl font-bold text-foreground">{header.title}</h1>
        </div>
        <p className="text-foreground-muted">{header.subtitle}</p>
      </motion.div>

      {/* Main Content */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.1 }}
      >
        <AnimatePresence mode="wait">
          {view === 'list' && (
            <motion.div
              key="list"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="space-y-8"
            >
              {/* Pinned Section */}
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <Pin size={20} className="text-indigo-400" />
                  <h2 className="text-xl font-semibold text-foreground">Pinned</h2>
                  <span className="text-sm text-foreground-muted">({pinnedCompanies.length}/{MAX_PINNED})</span>
                </div>

                {pinnedCompanies.length === 0 ? (
                  <GlassCard className="p-8 text-center">
                    <Pin size={32} className="mx-auto text-gray-500 mb-3" />
                    <p className="text-gray-400 text-sm">
                      Pin up to {MAX_PINNED} companies for quick access to their analysis.
                    </p>
                    <p className="text-gray-500 text-xs mt-1">
                      Use the pin button in the watchlist below to add companies.
                    </p>
                  </GlassCard>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <AnimatePresence>
                      {pinnedCompanies.map((company) => (
                        <PinnedCompanyCard
                          key={company.id}
                          companyId={company.id}
                          companyName={company.name}
                          companyTicker={company.ticker}
                          onUnpin={() => handleUnpinCompany(company.id)}
                          onClick={() => handleViewDetails(company.ticker)}
                        />
                      ))}
                    </AnimatePresence>
                  </div>
                )}
              </div>

              {/* Watchlist Table with Pin Support */}
              <WatchlistTable
                onCompare={handleCompare}
                onViewDetails={handleViewDetails}
                onPin={handlePinCompany}
                isPinned={isPinned}
                maxPinned={MAX_PINNED}
                pinnedCount={pinnedCompanies.length}
              />
            </motion.div>
          )}

          {view === 'comparison' && (
            <motion.div
              key="comparison"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
            >
              <ComparisonView
                tickers={comparisonTickers}
                onBack={() => setView('list')}
              />
            </motion.div>
          )}

          {view === 'details' && detailTicker && (
            <motion.div
              key="details"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
            >
              <CompanyDetails
                ticker={detailTicker}
                onBack={() => setView('list')}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <ProtectedLayout>
      <DashboardContent />
    </ProtectedLayout>
  );
}
