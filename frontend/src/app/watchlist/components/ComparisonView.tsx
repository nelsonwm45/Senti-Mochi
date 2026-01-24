'use client';

import { useState, useEffect } from 'react';
import { ArrowLeft, Loader2, TrendingUp, Wallet, Activity, ChevronDown, ChevronUp } from 'lucide-react';
import { GlassCard } from '@/components/ui/GlassCard';
import { getKeyMetrics, formatValue, formatPercent } from '../utils';

interface ComparisonViewProps {
  tickers: string[];
  onBack: () => void;
}



// Recommended order for financial statements to match Comparison View
const IS_ORDER = [
    'Total Revenue', 'Revenue', 'Cost Of Revenue', 'Gross Profit', 
    'Operating Expense', 'Operating Income', 'Net Non Operating Interest Income Expense',
    'Pretax Income', 'Tax Provision', 'Net Income Common Stockholders', 
    'Net Income', 'Diluted NI Available to Com Stockholders', 'Basic EPS', 'Diluted EPS',
    'EBITDA', 'EBIT'
];

const BS_ORDER = [
    'Total Assets', 'Current Assets', 'Cash And Cash Equivalents', 
    'Total Liabilities Net Minority Interest', 'Total Liabilities', 'Current Liabilities', 'Total Debt', 'Net Debt',
    'Total Equity Gross Minority Interest', 'Stockholders Equity',
    'Working Capital', 'Invested Capital'
];

const CF_ORDER = [
    'Operating Cash Flow', 'Investing Cash Flow', 'Financing Cash Flow',
    'Capital Expenditure', 'Free Cash Flow', 'End Cash Position',
    'Issuance Of Debt', 'Repayment Of Debt', 'Cash Dividends Paid'
];

const sortFinancialKeys = (keys: string[], orderList: string[]) => {
    return keys.sort((a, b) => {
        const idxA = orderList.indexOf(a);
        const idxB = orderList.indexOf(b);
        if (idxA !== -1 && idxB !== -1) return idxA - idxB;
        if (idxA !== -1) return -1;
        if (idxB !== -1) return 1;
        return a.localeCompare(b);
    });
};

export function ComparisonView({ tickers, onBack }: ComparisonViewProps) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showFull, setShowFull] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
        try {
            const query = tickers.map(t => `tickers=${t}`).join('&');
            const res = await fetch(`/api/v1/companies/compare?${query}`);
            const json = await res.json();
            setData(json);
        } catch (e) {
            console.error("Failed to compare", e);
        } finally {
            setLoading(false);
        }
    };
    if (tickers.length > 0) fetchData();
  }, [tickers]);

  if (loading) {
      return <div className="flex justify-center p-12"><Loader2 className="animate-spin text-white" size={32} /></div>;
  }

  if (data.length < 2) return <div className="text-white p-6">Could not load comparison data.</div>;

  const [c1, c2] = data;
  
  // Helper to extract latest value for a metric
  const getValue = (companyData: any, category: string, metricName: string) => {
      const cat = companyData[category];
      if (!cat) return null;
      const dates = Object.keys(cat).sort().reverse();
      const latestDate = dates[0];
      if (!latestDate) return null;
      
      const metrics = cat[latestDate];
      const key = Object.keys(metrics).find(k => k.toLowerCase().includes(metricName.toLowerCase()) || k === metricName);
      return key ? metrics[key] : null; 
  };
 
  const getLatestDate = (companyData: any, category: string) => {
      const cat = companyData[category];
      if (!cat) return 'N/A';
      const dates = Object.keys(cat).sort().reverse();
      return dates[0] || 'N/A';
  };

  const c1ISDate = getLatestDate(c1, 'income_statement');
  const c2ISDate = getLatestDate(c2, 'income_statement');
  
  const c1BSDate = getLatestDate(c1, 'balance_sheet');
  const c2BSDate = getLatestDate(c2, 'balance_sheet');

  const c1CFDate = getLatestDate(c1, 'cash_flow');
  const c2CFDate = getLatestDate(c2, 'cash_flow');

  const c1Metrics = getKeyMetrics(c1);
  const c2Metrics = getKeyMetrics(c2);

  const keyMetricRows = [
      { label: 'Total Revenue', v1: c1Metrics.totalRevenue, v2: c2Metrics.totalRevenue },
      { label: 'Net Income', v1: c1Metrics.netIncome, v2: c2Metrics.netIncome },
      { label: 'Net Profit Margin', v1: c1Metrics.netProfitMargin, v2: c2Metrics.netProfitMargin, isPercent: true },
      { label: 'Diluted EPS', v1: c1Metrics.dilutedEPS, v2: c2Metrics.dilutedEPS },
      { label: 'Cash & Equivalents', v1: c1Metrics.cashAndEquivalents, v2: c2Metrics.cashAndEquivalents },
      { label: 'Total Debt', v1: c1Metrics.totalDebt, v2: c2Metrics.totalDebt },
      { label: 'Operating Cash Flow', v1: c1Metrics.operatingCashFlow, v2: c2Metrics.operatingCashFlow },
      { label: 'Free Cash Flow', v1: c1Metrics.freeCashFlow, v2: c2Metrics.freeCashFlow },
  ];

  const renderFinancialSection = (title: string, icon: React.ReactNode, category: string, order: string[], c1Date: string, c2Date: string) => {
      return (
        <div className="bg-slate-900/50 p-6 rounded-2xl border border-white/10">
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    {icon}
                    {title}
                </h3>
                <span className="text-xs text-gray-500">All numbers in base currency</span>
            </div>
             {/* Date Row for Section */}
             <div className="grid grid-cols-3 gap-4 py-2 border-b border-white/5 px-4 mb-2 bg-white/[0.02] rounded-lg">
                <span className="text-gray-500 text-xs uppercase tracking-wider font-semibold">Report Date</span>
                <div className="text-right text-xs text-accent font-mono">Last updated: {c1Date}</div>
                <div className="text-right text-xs text-accent font-mono">Last updated: {c2Date}</div>
             </div>
            <div className="space-y-1">
                {(() => {
                    const allKeys = new Set<string>();
                    [c1, c2].forEach(c => {
                        const cCat = c[category];
                        if (cCat) {
                            const date = Object.keys(cCat).sort().reverse()[0];
                            if (date) Object.keys(cCat[date]).forEach(k => allKeys.add(k));
                        }
                    });

                    return sortFinancialKeys(Array.from(allKeys), order).map((key) => {
                        const v1 = getValue(c1, category, key);
                        const v2 = getValue(c2, category, key);
                        
                        let c1Better = false, c2Better = false;
                        if (v1 !== null && v2 !== null && v1 !== v2 && typeof v1 === 'number' && typeof v2 === 'number') {
                            const isExpense = key.toLowerCase().includes('expense') || key.toLowerCase().includes('cost') || key.toLowerCase().includes('debt') || key.toLowerCase().includes('liabilit');
                            if (isExpense) { c1Better = v1 < v2; c2Better = v2 < v1; }
                            else { c1Better = v1 > v2; c2Better = v2 > v1; }
                        }
                        const c1Color = c1Better ? 'text-green-400' : c2Better ? 'text-red-400' : 'text-gray-300';
                        const c2Color = c2Better ? 'text-green-400' : c1Better ? 'text-red-400' : 'text-gray-300';

                        return (
                            <div key={key} className="grid grid-cols-3 gap-4 py-2 border-b border-white/5 last:border-0 hover:bg-white/[0.02] group">
                                <span className="text-gray-400 font-medium text-sm group-hover:text-gray-300 transition-colors">{key}</span>
                                <div className="text-right"> <span className={`font-mono font-medium text-sm ${c1Color}`}>{formatValue(v1)}</span> </div>
                                <div className="text-right"> <span className={`font-mono font-medium text-sm ${c2Color}`}>{formatValue(v2)}</span> </div>
                            </div>
                        )
                    })
                })()}
            </div>
        </div>
      );
  };
  
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button onClick={onBack} className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors text-gray-300 hover:text-white">
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
            <div className="text-xs text-gray-500">{c1.sector}</div>
          </div>
          <div className="w-1/3 text-right">
            <div className="text-xl font-bold text-white mb-1">{c2.ticker}</div>
            <div className="text-xs text-gray-500">{c2.sector}</div>
          </div>
        </div>

        {/* Key Metrics Section */}
        <div className="bg-slate-900/50 p-6 rounded-2xl border border-white/10">
             <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold text-white">Key Metrics</h3>
                <span className="text-xs text-gray-500">Highlighted Fundamentals</span>
             </div>
             <div className="space-y-1">
                 {keyMetricRows.map((row) => {
                     // Helper for coloring
                     const getColor = (val: number | null | undefined, label: string) => {
                        if (label === 'Total Debt') return 'text-gray-200';
                        if (val === null || val === undefined) return 'text-white';
                        if (val > 0) return 'text-emerald-400';
                        if (val < 0) return 'text-rose-400';
                        return 'text-white';
                     };

                     const c1Color = getColor(row.v1, row.label);
                     const c2Color = getColor(row.v2, row.label);

                     return (
                     <div key={row.label} className="grid grid-cols-3 gap-4 py-2 border-b border-white/5 last:border-0 hover:bg-white/[0.02]">
                         <span className="text-gray-400 font-medium text-sm">{row.label}</span>
                         <div className="text-right">
                             <span className={`font-mono font-medium text-sm ${c1Color}`}>
                                 {row.isPercent ? formatPercent(row.v1) : formatValue(row.v1)}
                             </span>
                         </div>
                         <div className="text-right">
                             <span className={`font-mono font-medium text-sm ${c2Color}`}>
                                 {row.isPercent ? formatPercent(row.v2) : formatValue(row.v2)}
                             </span>
                         </div>
                     </div>
                 )})}
             </div>
        </div>

        {/* Toggle for Full Financials */}
         <button 
             onClick={() => setShowFull(!showFull)}
             className="w-full py-4 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-white font-medium flex items-center justify-center gap-2 transition-all"
         >
             {showFull ? (
                 <>
                    <ChevronUp size={20} />
                    Hide Full Annual Reports
                 </>
             ) : (
                 <>
                    <ChevronDown size={20} />
                    View Full Financial Statements
                 </>
             )}
         </button>

         {showFull && (
             <div className="space-y-8 animate-in fade-in slide-in-from-top-4 duration-300">
                {renderFinancialSection('Income Statement', <TrendingUp className="text-green-400" />, 'income_statement', IS_ORDER, c1ISDate, c2ISDate)}
                {renderFinancialSection('Balance Sheet', <Wallet className="text-blue-400" />, 'balance_sheet', BS_ORDER, c1BSDate, c2BSDate)}
                {renderFinancialSection('Cash Flow', <Activity className="text-purple-400" />, 'cash_flow', CF_ORDER, c1CFDate, c2CFDate)}
             </div>
         )}
      </div>
    </div>
  );
}
