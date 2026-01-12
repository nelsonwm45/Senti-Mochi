'use client';

import { GlassCard } from '@/components/ui/GlassCard';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';

const PORTFOLIO_DATA = [
  { name: 'Mon', value: 125000 },
  { name: 'Tue', value: 128000 },
  { name: 'Wed', value: 126000 },
  { name: 'Thu', value: 132000 },
  { name: 'Fri', value: 134500 },
  { name: 'Sat', value: 134500 },
  { name: 'Sun', value: 134500 },
];

export function PortfolioChart() {
  return (
    <GlassCard className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-foreground">Portfolio Value</h3>
          <p className="text-sm text-foreground-muted">Total Assets Overview</p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-accent">RM 134,500</p>
          <p className="text-xs text-green-500 font-medium">+7.6% this week</p>
        </div>
      </div>
      <div className="h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={PORTFOLIO_DATA}>
            <defs>
              <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
            <XAxis 
              dataKey="name" 
              stroke="#64748b" 
              fontSize={12}
              tickLine={false}
              axisLine={false}
              dy={10}
            />
            <YAxis 
              stroke="#64748b" 
              fontSize={12}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `${value / 1000}k`}
              dx={-10}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'rgba(17, 24, 39, 0.9)', 
                borderColor: 'rgba(255, 255, 255, 0.1)', 
                backdropFilter: 'blur(12px)',
                borderRadius: '12px',
                color: '#fff',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.5)'
              }}
              itemStyle={{ color: '#10b981' }}
              formatter={(value: any) => [`RM ${value.toLocaleString()}`, 'Value']}
              cursor={{ stroke: 'rgba(16, 185, 129, 0.5)', strokeWidth: 2 }}
            />
            <Area 
              type="monotone" 
              dataKey="value" 
              stroke="#10b981" 
              strokeWidth={3}
              fillOpacity={1} 
              fill="url(#colorValue)" 
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </GlassCard>
  );
}
