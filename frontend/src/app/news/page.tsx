'use client';

import { useEffect, useState } from 'react';
import ProtectedLayout from '@/components/layouts/ProtectedLayout';
import { newsApi, NewsItem } from '@/lib/api/news';
import { GlassCard } from '@/components/ui/GlassCard';
import { GlassBadge } from '@/components/ui/GlassBadge';
import { Loader2, Newspaper, ExternalLink } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

export default function NewsPage() {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchNews = async () => {
    try {
        const data = await newsApi.getAll();
        setNews(data);
    } catch (err: any) {
        setError(err?.message || 'Failed to fetch news');
    } finally {
        setLoading(false);
    }
  };

  useEffect(() => {
    fetchNews();
  }, []);

  if (loading) {
    return (
      <ProtectedLayout>
        <div className="flex justify-center items-center h-full">
            <Loader2 className="animate-spin text-accent" size={32} />
        </div>
      </ProtectedLayout>
    );
  }

  if (error) {
    return (
      <ProtectedLayout>
        <div className="flex flex-col justify-center items-center h-full gap-4">
            <div className="text-red-500 text-lg">Error: {error}</div>
            <button onClick={fetchNews} className="px-4 py-2 bg-accent text-white rounded">
              Retry
            </button>
        </div>
      </ProtectedLayout>
    );
  }

  return (
    <ProtectedLayout>
      <div className="space-y-6">
        <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-500/10 rounded-xl text-blue-500">
                <Newspaper size={24} />
            </div>
            <div>
                <h1 className="text-2xl font-bold text-foreground">Market News</h1>
                <p className="text-foreground-muted">Latest updates from global markets</p>
            </div>
        </div>

        <div className="grid grid-cols-1 gap-4">
            {news.length === 0 ? (
                <div className="text-center py-12 text-foreground-muted">
                    No news articles found.
                </div>
            ) : (
                news.map((item) => (
                    <GlassCard key={item.id} className="p-6 transition-colors hover:bg-white/5 group">
                        <div className="flex justify-between items-start gap-4">
                            <div className="flex-1">
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="text-xs font-mono text-accent bg-accent/10 px-2 py-0.5 rounded">
                                        {item.source}
                                    </span>
                                    {item.company_ticker && (
                                        <span className="text-xs font-mono text-foreground-muted bg-white/5 px-2 py-0.5 rounded">
                                            {item.company_ticker}
                                        </span>
                                    )}
                                    <span className="text-xs text-foreground-muted">
                                        {formatDistanceToNow(new Date(item.published_at), { addSuffix: true })}
                                    </span>
                                </div>
                                <h3 className="text-lg font-semibold text-foreground mb-2 group-hover:text-accent transition-colors">
                                    <a href={item.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2">
                                        {item.title}
                                        <ExternalLink size={14} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                                    </a>
                                </h3>
                                {item.summary && (
                                    <div className="mb-2">
                                        <h4 className="text-xs font-semibold text-accent uppercase mb-1">AI Summary</h4>
                                        <p className="text-sm text-foreground-muted leading-relaxed">
                                            {item.summary}
                                        </p>
                                    </div>
                                )}
                                {item.content_preview && (
                                    <div className="mt-2 pt-2 border-t border-white/5">
                                        <h4 className="text-xs font-semibold text-foreground-secondary uppercase mb-1">Preview</h4>
                                        <p className="text-xs text-foreground-muted/80 leading-relaxed line-clamp-3 font-mono">
                                            {item.content_preview}
                                        </p>
                                    </div>
                                )}
                            </div>
                            <GlassBadge variant={
                                item.sentiment === 'Positive' ? 'success' :
                                item.sentiment === 'Negative' || item.sentiment === 'Adverse' ? 'error' : 'default'
                            }>
                                {item.sentiment}
                            </GlassBadge>
                        </div>
                    </GlassCard>
                ))
            )}
        </div>
      </div>
    </ProtectedLayout>
  );
}
