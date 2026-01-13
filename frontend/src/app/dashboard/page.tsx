'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ProtectedLayout from '@/components/layouts/ProtectedLayout';
import apiClient from '@/lib/apiClient';

import {
  FileText,
  AlertTriangle,
  Clock,
  ArrowRight,
  ExternalLink,
  TrendingUp,
  Minus,
  TrendingDown,
  Newspaper
} from 'lucide-react';
import { GlassCard } from '@/components/ui/GlassCard';
import {
  PieChart, Pie, Cell, Legend, ResponsiveContainer, Tooltip
} from 'recharts';

interface WatchlistCompany {
  id: string;
  name: string;
  ticker: string;
  sector?: string;
  sub_sector?: string;
  website_url?: string;
}
import { newsApi, UnifiedFeedItem } from '@/lib/api/news';


function DashboardContent() {
  const router = useRouter();

  // ... (keep interfaces if needed, or remove if imported)

  const [unifiedFeed, setUnifiedFeed] = useState<UnifiedFeedItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [watchlistEmpty, setWatchlistEmpty] = useState(false);
  const [watchlistCompanies, setWatchlistCompanies] = useState<WatchlistCompany[]>([]);
  const [stats, setStats] = useState({
    bursa: 0,
    star: 0,
    nst: 0,
    total: 0
  });

  // Helper: Parse date string to timestamp
  const parseDateToTimestamp = (dateStr: string): number => {
    try {
      const date = new Date(dateStr);
      return date.getTime() / 1000;
    } catch {
      return Date.now() / 1000;
    }
  };

  // Helper: Format NST date
  const formatNSTDate = (timestamp: number): string => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleDateString('en-MY', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Helper: Decode HTML entities
  const decodeHtml = (html: string): string => {
    const txt = document.createElement('textarea');
    txt.innerHTML = html;
    return txt.value;
  };

  // Helper: Parse HTML link
  const parseHtmlLink = (htmlString: string): { text: string; link?: string } => {
    const decoded = decodeHtml(htmlString);
    const linkMatch = decoded.match(/<a[^>]+href=['"]([^'"]+)['"][^>]*>(.*?)<\/a>/i);
    if (linkMatch) {
      return {
        text: linkMatch[2].replace(/<[^>]*>/g, '').trim(),
        link: linkMatch[1]
      };
    }
    const text = decoded.replace(/<[^>]*>/g, '').trim();
    return { text };
  };

  // Fetch Bursa announcements (client-side)
  const fetchBursaAnnouncements = async (companies: WatchlistCompany[]) => {
    const articles: any[] = [];

    for (const company of companies) {
      const bursaCode = company.ticker.split('.')[0];
      const url = `https://www.bursamalaysia.com/api/v1/announcements/search?ann_type=company&company=${bursaCode}&cat=AR,ARCO&per_page=5&page=0`;

      try {
        const response = await fetch(url, {
          method: 'GET',
          headers: { 'Accept': 'application/json' },
        });

        if (!response.ok) continue;

        const data = await response.json();
        if (!data.data) continue;

        for (const item of data.data.slice(0, 5)) {
          const dateMatch = parseHtmlLink(item[1]);
          const titleMatch = parseHtmlLink(item[3]);
          const link = titleMatch.link ? `https://www.bursamalaysia.com${titleMatch.link}` : '';
          const idMatch = link.match(/ann_id=(\d+)/);
          const native_id = idMatch ? `bursa-${bursaCode}-${idMatch[1]}` : `bursa-${bursaCode}-${item[0]}`;

          let published_at = new Date().toISOString();
          try {
            const parsedDate = new Date(dateMatch.text);
            if (!isNaN(parsedDate.getTime())) {
              published_at = parsedDate.toISOString();
            }
          } catch (e) { }

          articles.push({
            company_id: company.id,
            source: 'bursa',
            native_id,
            title: titleMatch.text,
            url: link,
            published_at,
            content: titleMatch.text
          });
        }
      } catch (err) {
        console.warn(`Error fetching Bursa for ${company.name}:`, err);
      }
    }

    return articles;
  };

  // Fetch Star news (client-side)
  const fetchStarNews = async (companies: WatchlistCompany[]) => {
    const articles: any[] = [];

    for (const company of companies) {
      const query = encodeURIComponent(company.name);
      const url = `https://api.queryly.com/json.aspx?queryly_key=6ddd278bf17648ac&query=${query}&endindex=0&batchsize=5&showfaceted=true&extendeddatafields=paywalltype,isexclusive,kicker,kickerurl,summary,sponsor&timezoneoffset=-450`;

      try {
        const response = await fetch(url, {
          method: 'GET',
          headers: { 'Accept': 'application/json' },
        });

        if (!response.ok) continue;

        const text = await response.text();
        let data: any;

        if (text.includes('resultcallback')) {
          const match = text.match(/resultcallback\s*\(\s*({[\s\S]*})\s*\)/);
          if (match) data = JSON.parse(match[1]);
          else continue;
        } else {
          data = JSON.parse(text);
        }

        const items = data.items || [];
        for (const item of items.slice(0, 5)) {
          const published_at = new Date(item.pubdateunix * 1000).toISOString();

          articles.push({
            company_id: company.id,
            source: 'star',
            native_id: `star-${company.ticker}-${item._id}`,
            title: item.title,
            url: item.link,
            published_at,
            content: item.description || item.summary
          });
        }
      } catch (err) {
        console.warn(`Error fetching Star for ${company.name}:`, err);
      }
    }

    return articles;
  };

  // Fetch NST news (via Next.js API route)
  const fetchNSTNews = async (companies: WatchlistCompany[]) => {
    const articles: any[] = [];

    for (const company of companies) {
      const url = `/api/nst?keywords=${encodeURIComponent(company.name)}&category=&sort=DESC&page_size=5&page=0`;

      try {
        const response = await fetch(url, {
          method: 'GET',
          headers: { 'Accept': 'application/json' },
        });

        if (!response.ok) continue;

        const data = await response.json();
        const items = data.data || [];

        for (const item of items.slice(0, 5)) {
          const published_at = new Date(item.created * 1000).toISOString();

          articles.push({
            company_id: company.id,
            source: 'nst',
            native_id: `nst-${company.ticker}-${item.nid}`,
            title: item.title,
            url: item.url,
            published_at,
            content: item.field_article_lead
          });
        }
      } catch (err) {
        console.warn(`Error fetching NST for ${company.name}:`, err);
      }
    }

    return articles;
  };

  // Fetch user's watchlist and sync news
  useEffect(() => {
    const fetchWatchlist = async () => {
      try {
        const response = await apiClient.get('/api/v1/watchlist/my-watchlist');
        const companies = response.data;

        const watchlistHasCompanies = companies.length > 0;
        setWatchlistEmpty(!watchlistHasCompanies);

        if (watchlistHasCompanies) {
          setWatchlistCompanies(companies);
        }

        // Step 1: Load existing news from database first (fast)
        const cachedNewsData = await newsApi.getFeed(50, watchlistHasCompanies);

        setUnifiedFeed(cachedNewsData);

        // Calculate stats from cached data
        const cachedBursaCount = cachedNewsData.filter(i => i.type === 'bursa').length;
        const cachedStarCount = cachedNewsData.filter(i => i.type === 'star').length;
        const cachedNstCount = cachedNewsData.filter(i => i.type === 'nst').length;

        setStats({
          bursa: cachedBursaCount,
          star: cachedStarCount,
          nst: cachedNstCount,
          total: cachedNewsData.length
        });

        setLoading(false); // Show cached data immediately

        // Step 2: Fetch fresh news in background
        if (watchlistHasCompanies) {
          // Fetch news from all sources (client-side)
          const [bursaArticles, starArticles, nstArticles] = await Promise.all([
            fetchBursaAnnouncements(companies),
            fetchStarNews(companies),
            fetchNSTNews(companies)
          ]);

          const allArticles = [...bursaArticles, ...starArticles, ...nstArticles];

          // Send articles to backend for storage
          if (allArticles.length > 0) {
            try {
              await apiClient.post('/api/v1/news/store-articles', allArticles);

              // Step 3: Refresh feed with newly stored articles
              const updatedNewsData = await newsApi.getFeed(50, watchlistHasCompanies);

              setUnifiedFeed(updatedNewsData);

              // Update stats with fresh data
              const updatedBursaCount = updatedNewsData.filter(i => i.type === 'bursa').length;
              const updatedStarCount = updatedNewsData.filter(i => i.type === 'star').length;
              const updatedNstCount = updatedNewsData.filter(i => i.type === 'nst').length;

              setStats({
                bursa: updatedBursaCount,
                star: updatedStarCount,
                nst: updatedNstCount,
                total: updatedNewsData.length
              });
            } catch (storeErr) {
              console.warn('Failed to store articles:', storeErr);
            }
          }
        }

      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch watchlist');
        console.error('Error fetching watchlist:', err);
        setLoading(false);
      }
    };

    fetchWatchlist();
  }, []);



  // Get badge styling based on source type
  const getSourceBadge = (type: 'bursa' | 'star' | 'nst') => {
    switch (type) {
      case 'bursa':
        return {
          label: 'BURSA',
          color: 'text-emerald-500',
          bg: 'bg-emerald-500/10',
          icon: FileText
        };
      case 'star':
        return {
          label: 'THE STAR',
          color: 'text-blue-500',
          bg: 'bg-blue-500/10',
          icon: Newspaper
        };
      case 'nst':
        return {
          label: 'NST',
          color: 'text-purple-500',
          bg: 'bg-purple-500/10',
          icon: Newspaper
        };
    }
  };

  // Stats data
  const statsData = [
    {
      label: 'Total Items',
      value: stats.total.toString(),
      change: 'All sources',
      changeColor: 'text-emerald-500',
      icon: FileText,
      iconColor: 'text-emerald-500',
      iconBg: 'bg-emerald-500/10',
      borderColor: 'border-emerald-500/20'
    },
    {
      label: 'News Sources',
      value: '3',
      change: `${stats.bursa} Bursa, ${stats.star} Star, ${stats.nst} NST`,
      changeColor: 'text-blue-500',
      icon: Newspaper,
      iconColor: 'text-blue-500',
      iconBg: 'bg-blue-500/10',
      borderColor: 'border-blue-500/20'
    },
    {
      label: 'Last Updated',
      value: loading ? 'Loading...' : 'Just now',
      change: '',
      changeColor: '',
      icon: Clock,
      iconColor: 'text-emerald-500',
      iconBg: 'bg-emerald-500/10',
      borderColor: 'border-emerald-500/20'
    }
  ];

  // Calculate sentiment distribution from unified feed
  const sentimentData = [
    { name: 'Bursa', value: stats.bursa, color: '#10b981' }, // emerald-500
    { name: 'The Star', value: stats.star, color: '#3b82f6' }, // blue-500
    { name: 'NST', value: stats.nst, color: '#a855f7' }  // purple-500
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Dashboard</h1>
        <p className="text-foreground-muted">Real-time intelligence from Bursa filings and financial news</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {statsData.map((stat, index) => (
          <GlassCard key={index} className={`p-6 flex items-center gap-4 ${stat.borderColor} border`}>
            <div className={`p-3 rounded-xl ${stat.iconBg}`}>
              <stat.icon size={24} className={stat.iconColor} />
            </div>
            <div>
              <p className="text-sm text-foreground-muted">{stat.label}</p>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-foreground">{stat.value}</span>
                {stat.change && (
                  <span className={`text-xs ${stat.changeColor} font-medium`}>{stat.change}</span>
                )}
              </div>
            </div>
          </GlassCard>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Intelligence Feed - Now showing unified news from all sources */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-foreground">Intelligence Feed</h2>
            <span className="text-sm text-foreground-muted">
              {loading ? 'Loading...' : watchlistEmpty ? 'No companies in watchlist' : `Showing ${unifiedFeed.length} items from all sources`}
            </span>
          </div>

          {error && (
            <GlassCard className="p-6 border-red-500/50">
              <div className="flex items-center gap-2 text-red-500">
                <AlertTriangle size={20} />
                <span>Error loading news: {error}</span>
              </div>
            </GlassCard>
          )}

          {watchlistEmpty && !loading ? (
            <GlassCard className="p-12 border-amber-500/50 flex flex-col items-center justify-center text-center">
              <AlertTriangle size={40} className="text-amber-500 mb-4" />
              <h3 className="text-lg font-semibold text-foreground mb-2">Your Watchlist is Empty</h3>
              <p className="text-foreground-muted mb-6 max-w-md">
                Start adding companies to your watchlist to see their Bursa filings and financial news updates here.
              </p>
              <button
                onClick={() => router.push('/watchlist')}
                className="px-6 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg font-medium transition-colors"
              >
                Go to Watchlist
              </button>
            </GlassCard>
          ) : loading ? (
            <GlassCard className="p-6">
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
              </div>
            </GlassCard>
          ) : (
            <div className="space-y-4">
              {unifiedFeed.length === 0 ? (
                <GlassCard className="p-6">
                  <p className="text-center text-foreground-muted">No news items found for your watched companies</p>
                </GlassCard>
              ) : (
                unifiedFeed.map((item) => {
                  const badge = getSourceBadge(item.type);
                  const BadgeIcon = badge.icon;

                  // Get sentiment badge styles
                  const getSentimentBadge = (sentiment: any) => {
                    if (!sentiment) return null;

                    const label = sentiment.label.toLowerCase();
                    const score = sentiment.score || 0;

                    let bgColor = 'bg-gray-500/20';
                    let textColor = 'text-gray-300';
                    let icon = '◆';
                    let ariaLabel = 'Neutral sentiment';

                    if (label === 'positive') {
                      bgColor = 'bg-emerald-500/20';
                      textColor = 'text-emerald-400';
                      icon = '↑';
                      ariaLabel = 'Positive sentiment';
                    } else if (label === 'negative') {
                      bgColor = 'bg-red-500/20';
                      textColor = 'text-red-400';
                      icon = '↓';
                      ariaLabel = 'Negative sentiment';
                    }

                    return {
                      label,
                      score,
                      bgColor,
                      textColor,
                      icon,
                      ariaLabel,
                      confidence: sentiment.confidence || 0
                    };
                  };

                  const sentimentBadge = getSentimentBadge(item.sentiment);

                  return (
                    <GlassCard
                      key={item.id}
                      className="p-6 relative overflow-hidden group hover:border-emerald-500/30 transition-colors"
                    >
                      <div className="flex justify-between items-start mb-4">
                        <div className="flex-1">
                          <div className="flex items-baseline gap-2 mb-2">
                            <h3 className="text-lg font-bold text-foreground">{item.title}</h3>
                          </div>
                          <div className="flex items-center gap-3 flex-wrap">
                            <div className={`flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded ${badge.bg} ${badge.color} uppercase tracking-wider`}>
                              <BadgeIcon size={12} />
                              {badge.label}
                            </div>
                            {item.company && (
                              <span className="text-xs font-medium px-2 py-1 rounded bg-white/5 text-foreground-muted">
                                {item.company} {item.companyCode && `(${item.companyCode})`}
                              </span>
                            )}
                            {/* Show sentiment badge if available, or "analyzing" if not (but skip Bursa) */}
                            {item.type !== 'bursa' && (
                              sentimentBadge ? (
                                <div
                                  className={`flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded ${sentimentBadge.bgColor} ${sentimentBadge.textColor} uppercase tracking-wider group/sentiment relative`}
                                  title={`${sentimentBadge.label.charAt(0).toUpperCase() + sentimentBadge.label.slice(1)} (${sentimentBadge.score.toFixed(2)}) - Confidence: ${(sentimentBadge.confidence * 100).toFixed(0)}%`}
                                >
                                  <span>{sentimentBadge.icon}</span>
                                  <span>{sentimentBadge.label}</span>
                                  <span className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-black/80 text-white text-xs rounded whitespace-nowrap opacity-0 group-hover/sentiment:opacity-100 transition-opacity pointer-events-none">
                                    Score: {sentimentBadge.score.toFixed(2)} | Confidence: {(sentimentBadge.confidence * 100).toFixed(0)}%
                                  </span>
                                </div>
                              ) : (
                                <div
                                  className="flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded bg-blue-500/20 text-blue-400 uppercase tracking-wider"
                                  title="Sentiment analysis in progress"
                                >
                                  <span className="animate-pulse">⟳</span>
                                  <span>Analyzing</span>
                                </div>
                              )
                            )}
                          </div>
                        </div>
                        <span className="text-sm text-foreground-muted flex items-center gap-1 ml-4 whitespace-nowrap">
                          <Clock size={14} /> {item.date}
                        </span>
                      </div>

                      {item.description && (
                        <p className="text-foreground-secondary text-sm leading-relaxed mb-4 line-clamp-2">
                          {item.description}
                        </p>
                      )}

                      <div className="flex justify-end">
                        {item.link && (
                          <a
                            href={item.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-emerald-500 hover:text-emerald-400 text-sm font-medium flex items-center gap-1 transition-colors"
                          >
                            View Source <ExternalLink size={14} />
                          </a>
                        )}
                      </div>
                    </GlassCard>
                  );
                })
              )}
            </div>
          )}
        </div>

        {/* Sidebar: Source Distribution */}
        <div>
          <GlassCard className="p-6 h-fit sticky top-6">
            <h3 className="text-lg font-semibold text-foreground mb-6">Source Distribution</h3>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={sentimentData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                    stroke="none"
                  >
                    {sentimentData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(17, 24, 39, 0.9)',
                      borderColor: 'rgba(255, 255, 255, 0.1)',
                      backdropFilter: 'blur(12px)',
                      borderRadius: '12px',
                      color: '#fff'
                    }}
                    itemStyle={{ color: '#e2e8f0' }}
                  />
                  <Legend
                    verticalAlign="bottom"
                    height={36}
                    iconType="circle"
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-6 space-y-3">
              <p className="text-sm text-foreground-muted text-center">
                News items from {stats.bursa} Bursa, {stats.star} The Star, and {stats.nst} NST
              </p>
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <ProtectedLayout>
      <DashboardContent />
    </ProtectedLayout>
  );
}
