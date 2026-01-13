'use client';

import { ArrowLeft } from 'lucide-react';
import { motion } from 'framer-motion';
import { Company, mockCompanies, FinancialMetric } from '@/lib/mockData';
import { GlassCard } from '@/components/ui/GlassCard';

interface ComparisonViewProps {
  tickers: string[];
  onBack: () => void;
}

export function ComparisonView({ tickers, onBack }: ComparisonViewProps) {
  const c1 = mockCompanies.find((c) => c.ticker === tickers[0]);
  const c2 = mockCompanies.find((c) => c.ticker === tickers[1]);

  if (!c1 || !c2) return <div>Data missing</div>;

  const renderMetricRow = (
    label: string,
    m1: FinancialMetric,
    m2: FinancialMetric,
    isHigherBetter: boolean = true
  ) => {
    // Determine winner
    let c1Better = false;
    let c2Better = false;

    if (m1.value !== m2.value) {
      if (isHigherBetter) {
        c1Better = m1.value > m2.value;
        c2Better = m2.value > m1.value;
      } else {
        c1Better = m1.value < m2.value;
        c2Better = m2.value < m1.value;
      }
    }

    const c1Color = c1Better ? 'text-green-400' : c2Better ? 'text-red-400' : 'text-gray-300';
    const c2Color = c2Better ? 'text-green-400' : c1Better ? 'text-red-400' : 'text-gray-300';

    return (
      <div className="flex justify-between items-center py-4 border-b border-white/5 last:border-0 hover:bg-white/[0.02]">
        <div className="text-gray-400 font-medium w-1/3">{label}</div>
        <div className={`w-1/3 text-right font-mono font-medium ${c1Color} transition-colors`}>
          {m1.displayValue}
        </div>
        <div className={`w-1/3 text-right font-mono font-medium ${c2Color} transition-colors`}>
          {m2.displayValue}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button
          onClick={onBack}
          className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors text-gray-300 hover:text-white"
        >
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-2xl font-bold text-white">Financial Side-by-Side</h1>
      </div>

      <div className="grid grid-cols-1 gap-8">
        {/* Header Row */}
        <div className="flex justify-between items-end pb-4 border-b border-white/10 px-6">
          <div className="w-1/3 text-sm font-semibold text-gray-400 tracking-wider">METRIC</div>
          <div className="w-1/3 text-right">
            <div className="text-xl font-bold text-white mb-1">{c1.ticker}</div>
            <div className="text-xs text-gray-500">{c1.financials.quarter}</div>
          </div>
          <div className="w-1/3 text-right">
            <div className="text-xl font-bold text-white mb-1">{c2.ticker}</div>
            <div className="text-xs text-gray-500">{c2.financials.quarter}</div>
          </div>
        </div>

        <GlassCard className="p-6">
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">Income Statement</h2>
          {renderMetricRow('Revenue', c1.financials.incomeStatement.revenue, c2.financials.incomeStatement.revenue, true)}
          {renderMetricRow('Net Profit', c1.financials.incomeStatement.netProfit, c2.financials.incomeStatement.netProfit, true)}
          {renderMetricRow('Net Margin', c1.financials.incomeStatement.netMargin, c2.financials.incomeStatement.netMargin, true)}
        </GlassCard>

        <GlassCard className="p-6">
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">Balance Sheet</h2>
          {renderMetricRow('Total Assets', c1.financials.balanceSheet.totalAssets, c2.financials.balanceSheet.totalAssets, true)}
          {renderMetricRow('Total Liabilities', c1.financials.balanceSheet.totalLiabilities, c2.financials.balanceSheet.totalLiabilities, false)}
          {renderMetricRow('ROE', c1.financials.balanceSheet.roe, c2.financials.balanceSheet.roe, true)}
          {renderMetricRow('Debt/Equity', c1.financials.balanceSheet.debtToEquity, c2.financials.balanceSheet.debtToEquity, false)}
        </GlassCard>

        <GlassCard className="p-6">
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">Cash Flow</h2>
          {renderMetricRow('Operating CF', c1.financials.cashFlow.operatingCf, c2.financials.cashFlow.operatingCf, true)}
          {renderMetricRow('Investing CF', c1.financials.cashFlow.investingCf, c2.financials.cashFlow.investingCf, true)} {/* Context dependent, usually close to 0 is not necessarily better. Assuming standard 'more positive' check for now */}
          {renderMetricRow('Financing CF', c1.financials.cashFlow.financingCf, c2.financials.cashFlow.financingCf, true)}
        </GlassCard>
      </div>
    </div>
  );
}
