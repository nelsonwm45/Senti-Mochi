'use client';

import { GlassCard } from '@/components/ui/GlassCard';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';

interface FinancialsTabProps {
  ratios: any[];
}

export function FinancialsTab({ ratios }: FinancialsTabProps) {
  // Group by ratio name for multiple charts or select one
  // For MVP, lets show one chart for a specific ratio if available, e.g. "Current Ratio"
  // Or just map all ratios to a simple table if chart data is sparse.
  
  // Let's do a table for now as it's cleaner for diverse ratios
  
  return (
    <div className="space-y-6">
      <GlassCard className="p-6">
        <h3 className="text-lg font-semibold mb-4">Financial Ratios</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-white/10 text-foreground-muted text-sm">
                <th className="py-2">Ratio</th>
                <th className="py-2">Period</th>
                <th className="py-2 text-right">Value</th>
              </tr>
            </thead>
            <tbody>
              {ratios.length > 0 ? ratios.map((r, i) => (
                <tr key={i} className="border-b border-white/5 last:border-0 hover:bg-white/5 transition-colors">
                  <td className="py-3 text-foreground font-medium">{r.name}</td>
                  <td className="py-3 text-foreground-muted">{r.period}</td>
                  <td className="py-3 text-right text-accent font-mono">{r.value.toFixed(2)}</td>
                </tr>
              )) : (
                <tr>
                   <td colSpan={3} className="py-4 text-center text-foreground-muted">No financial data available</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </GlassCard>
      
      {/* Placeholder for Graph */}
      <GlassCard className="p-6 min-h-[300px] flex items-center justify-center">
        <p className="text-foreground-muted">Trend Analysis Graph (Coming Soon)</p>
      </GlassCard>
    </div>
  );
}
