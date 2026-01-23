'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { WatchlistTable } from './components/WatchlistTable';
import { ComparisonView } from './components/ComparisonView';
import { CompanyDetails } from './components/CompanyDetails';

type ViewState = 'list' | 'comparison' | 'details';

import ProtectedLayout from '@/components/layouts/ProtectedLayout';

import { useSearchParams } from 'next/navigation';

export default function WatchlistPage() {
  const searchParams = useSearchParams();
  const initialTicker = searchParams.get('ticker');

  const [view, setView] = useState<ViewState>(initialTicker ? 'details' : 'list');
  const [comparisonTickers, setComparisonTickers] = useState<string[]>([]);
  const [detailTicker, setDetailTicker] = useState<string | null>(initialTicker);

  // Update state when URL changes (optional but good for consistency)
  useEffect(() => {
    const ticker = searchParams.get('ticker');
    if (ticker) {
      setDetailTicker(ticker);
      setView('details');
    }
  }, [searchParams]);

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

  return (
    <ProtectedLayout>
      <div className="container mx-auto px-4 py-8">
        <AnimatePresence mode="wait">
          {view === 'list' && (
            <motion.div
              key="list"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
            >
              <WatchlistTable
                onCompare={handleCompare}
                onViewDetails={handleViewDetails}
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
      </div>
    </ProtectedLayout>
  );
}
