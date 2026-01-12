'use client';

import { GlassCard } from '@/components/ui/GlassCard';
import { GlassBadge } from '@/components/ui/GlassBadge';
import { GlassButton } from '@/components/ui/GlassButton';
import { formatDistanceToNow } from 'date-fns';
import { ExternalLink } from 'lucide-react';

interface NewsTabProps {
  news: any[];
}

export function NewsTab({ news }: NewsTabProps) {
  return (
    <div className="space-y-4">
      {news.length > 0 ? news.map((item) => (
        <GlassCard key={item.id} className="p-4 flex flex-col md:flex-row gap-4 group">
           <div className="flex-1">
             <div className="flex items-center gap-2 mb-2">
               <span className="text-xs text-foreground-muted">{new Date(item.published_at).toLocaleDateString()}</span>
               <GlassBadge variant={
                  item.sentiment === 'Positive' ? 'success' : 
                  item.sentiment === 'Negative' ? 'error' : 'default'
               } size="sm">
                 {item.sentiment}
               </GlassBadge>
             </div>
             <h4 className="text-lg font-medium text-foreground mb-2 group-hover:text-accent transition-colors">
               <a href={item.url} target="_blank" rel="noopener noreferrer" className="hover:underline">
                 {item.title}
               </a>
             </h4>
             <p className="text-sm text-foreground-muted line-clamp-2">
               {/* Summary could go here if available */}
               Click to read the full article at the source.
             </p>
           </div>
           <div className="flex items-center justify-end md:justify-center">
             <a href={item.url} target="_blank" rel="noopener noreferrer">
               <GlassButton size="icon" variant="ghost">
                 <ExternalLink size={20} />
               </GlassButton>
             </a>
           </div>
        </GlassCard>
      )) : (
        <div className="text-center py-12 text-foreground-muted">
          No news available.
        </div>
      )}
    </div>
  );
}
