'use client';

import { useState, useEffect } from 'react';
import { ArrowLeft, Loader2, TrendingUp, Wallet, Activity } from 'lucide-react';
import { GlassCard } from '@/components/ui/GlassCard';

interface ComparisonViewProps {
  tickers: string[];
  onBack: () => void;
}

// Simple formatter for large numbers
const formatValue = (val: number) => {
    if (val === undefined || val === null) return '-';
    // Show full number with commas per user request
    return val.toLocaleString();
};

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

  useEffect(() => {
    const fetchData = async () => {
        try {
            const query = tickers.map(t => `tickers=${t}`).join('&');
            const res = await fetch(`http://localhost:8000/api/v1/companies/compare?${query}`);
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
      if (!cat) return 0;
      const dates = Object.keys(cat).sort().reverse();
      const latestDate = dates[0];
      if (!latestDate) return 0;
      
      const metrics = cat[latestDate];
      const key = Object.keys(metrics).find(k => k.toLowerCase().includes(metricName.toLowerCase()) || k === metricName);
      return key ? metrics[key] : 0;
  };

  const c1Revenue = getValue(c1, 'income_statement', 'Total Revenue'); 
  // ... (keeping legacy getValue but using dynamic below)
  
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
            <div className="text-xs text-gray-500">{c1.sector}</div>
          </div>
          <div className="w-1/3 text-right">
            <div className="text-xl font-bold text-white mb-1">{c2.ticker}</div>
            <div className="text-xs text-gray-500">{c2.sector}</div>
          </div>
        </div>

            {/* Financials: Income Statement */}
            <div className="bg-slate-900/50 p-6 rounded-2xl border border-white/10">
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-xl font-bold text-white flex items-center gap-2">
                        <TrendingUp className="text-green-400" />
                        Income Statement
                    </h3>
                    <span className="text-xs text-gray-500">All numbers in base currency</span>
                </div>
                 <div className="space-y-1">
                  {(() => {
                      // Get union of all keys from both companies for this category
                      const allKeys = new Set<string>();
                      const cat = 'income_statement';
                      
                      [c1, c2].forEach(c => {
                          const cCat = c[cat];
                          if (cCat) {
                              const date = Object.keys(cCat).sort().reverse()[0];
                              if (date) {
                                  Object.keys(cCat[date]).forEach(k => allKeys.add(k));
                              }
                          }
                      });

                      const sortedKeys = sortFinancialKeys(Array.from(allKeys), IS_ORDER);

                      return sortedKeys.map((key) => {
                          // Get values
                          const v1 = getValue(c1, cat, key);
                          const v2 = getValue(c2, cat, key);
                          
                          // Optimization: Hide if both are 0 or empty? User wants "more data", so show all for now.
                          
                           let c1Better = false;
                           let c2Better = false;
                           if (v1 !== v2 && typeof v1 === 'number' && typeof v2 === 'number') {
                               // Naive assumption: Higher is better for Income/Revenue. 
                               // Not true for Expenses, but hard to know generic semantic here.
                               // Let's just color higher vs lower or remove color if ambiguous?
                               // Let's stick to neutral/no color for values, just comparison.
                               // Actually user liked the red/green in previous version.
                               // Let's default to Higher = Green for now, except if key contains 'Expense' or 'Cost'.
                               const isExpense = key.toLowerCase().includes('expense') || key.toLowerCase().includes('cost') || key.toLowerCase().includes('debt');
                               if (isExpense) {
                                   c1Better = v1 < v2; 
                                   c2Better = v2 < v1;
                               } else {
                                   c1Better = v1 > v2;
                                   c2Better = v2 > v1;
                               }
                           }
                            const c1Color = c1Better ? 'text-green-400' : c2Better ? 'text-red-400' : 'text-gray-300';
                            const c2Color = c2Better ? 'text-green-400' : c1Better ? 'text-red-400' : 'text-gray-300';

                          return (
                            <div key={key} className="grid grid-cols-3 gap-4 py-2 border-b border-white/5 last:border-0 hover:bg-white/[0.02] group">
                                <span className="text-gray-400 font-medium text-sm group-hover:text-gray-300 transition-colors">{key}</span>
                                <div className="text-right">
                                    <span className={`font-mono font-medium text-sm ${c1Color}`}>
                                        {formatValue(v1)}
                                    </span>
                                </div>
                                <div className="text-right">
                                    <span className={`font-mono font-medium text-sm ${c2Color}`}>
                                        {formatValue(v2)}
                                    </span>
                                </div>
                            </div>
                          );
                      });
                  })()}
                 </div>
            </div>

             {/* Financials: Balance Sheet */}
            <div className="bg-slate-900/50 p-6 rounded-2xl border border-white/10">
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-xl font-bold text-white flex items-center gap-2">
                            <Wallet className="text-blue-400" />
                        Balance Sheet
                    </h3>
                    <span className="text-xs text-gray-500">All numbers in base currency</span>
                </div>
                <div className="space-y-1">
                    {(() => {
                        const allKeys = new Set<string>();
                        const cat = 'balance_sheet';
                        [c1, c2].forEach(c => {
                            const cCat = c[cat];
                            if (cCat) {
                                const date = Object.keys(cCat).sort().reverse()[0];
                                if (date) Object.keys(cCat[date]).forEach(k => allKeys.add(k));
                            }
                        });

                        return sortFinancialKeys(Array.from(allKeys), BS_ORDER).map((key) => {
                            const v1 = getValue(c1, cat, key);
                            const v2 = getValue(c2, cat, key);
                            // Simple comparison (Higher Assets = Green, Higher Debt = Red?)
                            // Use same naive heuristic logic
                            let c1Better = false, c2Better = false;
                            if (v1 !== v2 && typeof v1 === 'number' && typeof v2 === 'number') {
                                const isBad = key.toLowerCase().includes('debt') || key.toLowerCase().includes('liabilit');
                                if (isBad) { c1Better = v1 < v2; c2Better = v2 < v1; }
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

            {/* Financials: Cash Flow */}
            <div className="bg-slate-900/50 p-6 rounded-2xl border border-white/10">
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-xl font-bold text-white flex items-center gap-2">
                        <Activity className="text-purple-400" />
                        Cash Flow
                    </h3>
                    <span className="text-xs text-gray-500">All numbers in base currency</span>
                </div>
                <div className="space-y-1">
                {(() => {
                        const allKeys = new Set<string>();
                        const cat = 'cash_flow';
                        [c1, c2].forEach(c => {
                            const cCat = c[cat];
                            if (cCat) {
                                const date = Object.keys(cCat).sort().reverse()[0];
                                if (date) Object.keys(cCat[date]).forEach(k => allKeys.add(k));
                            }
                        });

                        return sortFinancialKeys(Array.from(allKeys), CF_ORDER).map((key) => {
                            const v1 = getValue(c1, cat, key);
                            const v2 = getValue(c2, cat, key);
                            // Cash flow usually higher better
                            let c1Better = false, c2Better = false;
                            if (v1 !== v2 && typeof v1 === 'number' && typeof v2 === 'number') {
                                 c1Better = v1 > v2; c2Better = v2 > v1;
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
      </div>
    </div>
  );
}
