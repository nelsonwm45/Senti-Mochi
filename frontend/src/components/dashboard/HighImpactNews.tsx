'use client';

import { GlassCard } from '@/components/ui/GlassCard';
import { Badge } from 'lucide-react'; // Placeholder, replace with custom badge if needed
import { GlassBadge } from '@/components/ui/GlassBadge';
import { formatDistanceToNow } from 'date-fns';

interface NewsItem {
  id: string;
  source: string;
  title: string;
  sentiment: 'Positive' | 'Negative' | 'Neutral';
  publishedAt: Date;
}

// Mock Data until API is ready
const MOCK_NEWS: NewsItem[] = [
  { id: '1', source: 'The Edge', title: 'Maybank reports record Q4 earnings driven by loan growth', sentiment: 'Positive', publishedAt: new Date(Date.now() - 1000 * 60 * 30) },
  { id: '2', source: 'Bloomberg', title: 'Tech sector faces headwinds as global demand slows', sentiment: 'Negative', publishedAt: new Date(Date.now() - 1000 * 60 * 60 * 2) },
  { id: '3', source: 'Bursa', title: 'CIMB announces new sustainability framework', sentiment: 'Positive', publishedAt: new Date(Date.now() - 1000 * 60 * 60 * 5) },
];

export function HighImpactNews() {
  return (
    <GlassCard className="p-6 h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-foreground">High Impact News</h3>
        <span className="text-xs text-accent cursor-pointer hover:underline">View All</span>
      </div>
      
      <div className="space-y-4 flex-1 overflow-auto pr-2 custom-scrollbar">
        {MOCK_NEWS.map((item) => (
          <div key={item.id} className="group p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors border border-transparent hover:border-white/10">
            <div className="flex justify-between items-start gap-2 mb-2">
              <span className="text-xs font-medium text-foreground-muted uppercase tracking-wider">{item.source}</span>
              <GlassBadge variant={
                item.sentiment === 'Positive' ? 'success' : 
                item.sentiment === 'Negative' ? 'error' : 'default'
              } className="text-[10px] px-2 py-0.5 h-auto">
                {item.sentiment}
              </GlassBadge>
            </div>
            <h4 className="text-sm font-medium text-foreground leading-snug group-hover:text-accent transition-colors mb-2">
              {item.title}
            </h4>
            <span className="text-xs text-foreground-muted">
              {formatDistanceToNow(item.publishedAt, { addSuffix: true })}
            </span>
          </div>
        ))}
      </div>
    </GlassCard>
  );
}
