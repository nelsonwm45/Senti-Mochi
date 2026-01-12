'use client';

import { useEffect, useState } from 'react';
import { GlassCard } from '@/components/ui/GlassCard';
import { GlassBadge } from '@/components/ui/GlassBadge';
import { formatDistanceToNow } from 'date-fns';
import Link from 'next/link';
import { newsApi, NewsItem } from '@/lib/api/news';
import { Loader2 } from 'lucide-react';

export function HighImpactNews() {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchNews();
  }, []);

  const fetchNews = async () => {
    try {
      const data = await newsApi.getAll();
      setNews(data.slice(0, 5)); // Limit to 5 for widget
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <GlassCard className="p-6 h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-foreground">High Impact News</h3>
        <Link href="/news">
          <span className="text-xs text-accent cursor-pointer hover:underline">View All</span>
        </Link>
      </div>
      
      <div className="space-y-4 flex-1 overflow-auto pr-2 custom-scrollbar">
        {isLoading ? (
          <div className="flex justify-center items-center h-full">
             <Loader2 className="w-5 h-5 animate-spin text-accent" />
          </div>
        ) : news.length === 0 ? (
          <div className="text-center text-foreground-muted text-sm py-8">
            No news available.
          </div>
        ) : (
          news.map((item) => (
            <div key={item.id} className="group p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors border border-transparent hover:border-white/10">
              <div className="flex justify-between items-start gap-2 mb-2">
                <span className="text-xs font-medium text-foreground-muted uppercase tracking-wider">{item.source}</span>
                <GlassBadge variant={
                  item.sentiment === 'Positive' ? 'success' : 
                  item.sentiment === 'Negative' || item.sentiment === 'Adverse' ? 'error' : 'default'
                } className="text-[10px] px-2 py-0.5 h-auto">
                  {item.sentiment}
                </GlassBadge>
              </div>
              <h4 className="text-sm font-medium text-foreground leading-snug group-hover:text-accent transition-colors mb-2">
                <a href={item.url} target="_blank" rel="noopener noreferrer">
                  {item.title}
                </a>
              </h4>
              <span className="text-xs text-foreground-muted">
                {formatDistanceToNow(new Date(item.published_at), { addSuffix: true })}
              </span>
            </div>
          ))
        )}
      </div>
    </GlassCard>
  );
}
