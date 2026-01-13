'use client';

import { useState } from 'react';
import { ArrowLeft, FileText, Upload, PieChart, BarChart3, TrendingUp } from 'lucide-react';
import { mockCompanies } from '@/lib/mockData';
import { GlassCard } from '@/components/ui/GlassCard';

interface CompanyDetailsProps {
  ticker: string;
  onBack: () => void;
}

const tabs = [
  { id: 'details', label: 'Details', icon: FileText },
  { id: 'uploads', label: 'Uploads', icon: Upload },
  { id: 'is', label: 'Income Statement', icon: BarChart3 },
  { id: 'bs', label: 'Balance Sheet', icon: PieChart },
  { id: 'cf', label: 'Cash Flow', icon: TrendingUp },
];

export function CompanyDetails({ ticker, onBack }: CompanyDetailsProps) {
  const company = mockCompanies.find((c) => c.ticker === ticker);
  const [activeTab, setActiveTab] = useState('details');

  if (!company) return <div>Company not found</div>;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={onBack}
          className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors text-gray-300 hover:text-white"
        >
          <ArrowLeft size={20} />
        </button>
        <div className="flex items-center gap-4">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold text-xl shadow-lg ${company.logo || 'bg-gradient-primary'}`}>
                {company.ticker[0]}
            </div>
            <div>
                 <h1 className="text-2xl font-bold text-white leading-tight">{company.name}</h1>
                 <div className="flex gap-2 text-sm text-gray-400">
                    <span>{company.ticker}</span>
                    <span>•</span>
                    <span>{company.sector}</span>
                 </div>
            </div>
        </div>
      </div>

       {/* Tabs */}
      <div className="flex gap-1 overflow-x-auto pb-2 border-b border-white/10">
        {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
                <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 px-4 py-2.5 rounded-t-lg transition-all border-b-2 whitespace-nowrap ${
                        isActive 
                        ? 'border-accent text-accent bg-white/5' 
                        : 'border-transparent text-gray-400 hover:text-white hover:bg-white/5'
                    }`}
                >
                    <Icon size={16} />
                    <span className="font-medium">{tab.label}</span>
                </button>
            )
        })}
      </div>

       {/* Content */}
       <div className="min-h-[400px]">
            {activeTab === 'details' && (
                <GlassCard className="space-y-4">
                     <h3 className="text-lg font-semibold text-white">About {company.name}</h3>
                     <p className="text-gray-300 leading-relaxed">{company.description}</p>
                     
                     <div className="grid grid-cols-2 gap-4 mt-6">
                         <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                            <div className="text-sm text-gray-400 mb-1">Market Cap</div>
                            <div className="text-xl font-mono text-white">{company.marketCap}</div>
                         </div>
                         <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                             <div className="text-sm text-gray-400 mb-1">Latest Reporting</div>
                             <div className="text-xl font-mono text-white">{company.financials.quarter}</div>
                         </div>
                     </div>
                </GlassCard>
            )}

            {activeTab === 'uploads' && (
                <GlassCard className="flex flex-col items-center justify-center py-12 text-gray-400">
                    <Upload size={48} className="mb-4 opacity-50" />
                    <p>No documents uploaded yet.</p>
                </GlassCard>
            )}

             {activeTab === 'is' && (
                <GlassCard>
                     <h3 className="text-lg font-semibold text-white mb-4">Income Statement</h3>
                     <div className="space-y-2">
                        {Object.entries(company.financials.incomeStatement).map(([key, metric]) => (
                            <div key={key} className="flex justify-between py-3 border-b border-white/5 last:border-0">
                                <span className="text-gray-400">{metric.label}</span>
                                <span className="font-mono text-white">{metric.displayValue}</span>
                            </div>
                        ))}
                     </div>
                </GlassCard>
            )}

            {activeTab === 'bs' && (
                <GlassCard>
                     <h3 className="text-lg font-semibold text-white mb-4">Balance Sheet</h3>
                     <div className="space-y-2">
                        {Object.entries(company.financials.balanceSheet).map(([key, metric]) => (
                            <div key={key} className="flex justify-between py-3 border-b border-white/5 last:border-0">
                                <span className="text-gray-400">{metric.label}</span>
                                <span className="font-mono text-white">{metric.displayValue}</span>
                            </div>
                        ))}
                     </div>
                </GlassCard>
            )}

             {activeTab === 'cf' && (
                <GlassCard>
                     <h3 className="text-lg font-semibold text-white mb-4">Cash Flow</h3>
                     <div className="space-y-2">
                        {Object.entries(company.financials.cashFlow).map(([key, metric]) => (
                            <div key={key} className="flex justify-between py-3 border-b border-white/5 last:border-0">
                                <span className="text-gray-400">{metric.label}</span>
                                <span className="font-mono text-white">{metric.displayValue}</span>
                            </div>
                        ))}
                     </div>
                </GlassCard>
            )}
       </div>
    </div>
  );
}
