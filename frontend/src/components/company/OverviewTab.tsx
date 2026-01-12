'use client';

import { GlassCard } from '@/components/ui/GlassCard';
import { FileText } from 'lucide-react';

interface OverviewTabProps {
  company: any;
  filings: any[];
}

export function OverviewTab({ company, filings }: OverviewTabProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
      {/* Summary Section */}
      <div className="space-y-6">
        <GlassCard className="p-6">
          <h3 className="text-lg font-semibold mb-4 text-foreground">Company Summary</h3>
          <p className="text-foreground-secondary leading-relaxed">
            {company.summary || "No summary available for this company."}
          </p>
        </GlassCard>

        <GlassCard className="p-6">
          <h3 className="text-lg font-semibold mb-4 text-foreground">Key Stats</h3>
          <div className="grid grid-cols-2 gap-4">
             <div>
               <p className="text-xs text-foreground-muted">Market Cap</p>
               <p className="text-xl font-mono text-accent">
                 {company.market_cap ? `RM ${(company.market_cap / 1e9).toFixed(1)}B` : 'N/A'}
               </p>
             </div>
             <div>
               <p className="text-xs text-foreground-muted">Sector</p>
               <p className="text-xl text-foreground">{company.sector || 'N/A'}</p>
             </div>
          </div>
        </GlassCard>
      </div>

      {/* Recent Filings */}
      <GlassCard className="p-6">
        <h3 className="text-lg font-semibold mb-4 text-foreground">Recent Filings</h3>
        <div className="space-y-4">
          {filings.length > 0 ? filings.map((f: any) => (
            <div key={f.id} className="p-3 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 transition-colors flex gap-3">
              <div className="p-2 bg-blue-500/20 text-blue-400 rounded-lg h-fit">
                <FileText size={18} />
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">{f.type.replace('_', ' ')}</p>
                <p className="text-xs text-foreground-muted mb-1">{new Date(f.date).toLocaleDateString()}</p>
                <p className="text-xs text-foreground-secondary line-clamp-2">
                   {f.summary}
                </p>
              </div>
            </div>
          )) : (
            <p className="text-foreground-muted">No recent filings.</p>
          )}
        </div>
      </GlassCard>
    </div>
  );
}
