'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ProtectedLayout from '@/components/layouts/ProtectedLayout';
import apiClient from '@/lib/apiClient';
import usePersona from '@/hooks/usePersona';
import {
  InvestorLayout,
  RelationshipManagerLayout,
  CreditRiskLayout,
  MarketAnalystLayout
} from '@/components/dashboard';

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
import { toast } from 'react-hot-toast';
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


const WhatsAppIcon = ({ size = 24, className = "" }: { size?: number, className?: string }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
    stroke="none"
  >
    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
  </svg>
);

function DashboardContent() {
  const router = useRouter();
  const { persona, isLoading: personaLoading } = usePersona();

  // ... (keep interfaces if needed, or remove if imported)

  const [unifiedFeed, setUnifiedFeed] = useState<UnifiedFeedItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [watchlistEmpty, setWatchlistEmpty] = useState(false);
  const [watchlistCompanies, setWatchlistCompanies] = useState<WatchlistCompany[]>([]);
  const [activeTab, setActiveTab] = useState<'all' | 'alerts' | 'positive' | 'negative' | 'neutral'>('all');
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>('all');
  const [stats, setStats] = useState({
    bursa: 0,
    star: 0,
    nst: 0,
    edge: 0,
    total: 0
  });
  const [hasFetched, setHasFetched] = useState(false);  // Prevent duplicate fetches

  // WhatsApp Share Handler
  const handleWhatsAppShare = (item: UnifiedFeedItem) => {
    // Construct message with summary and link
    const summary = item.description || item.title || '';
    const link = item.link || '';
    const text = `*AI Summary*: ${summary}\n\n*Source*: ${link}`;

    // Copy to clipboard
    navigator.clipboard.writeText(text).then(() => {
      toast.success('Copied to clipboard & opening WhatsApp', {
        style: {
          background: '#10B981',
          color: '#fff',
        },
        iconTheme: {
          primary: '#fff',
          secondary: '#10B981',
        },
      });

      // Open WhatsApp Web
      const encodedText = encodeURIComponent(text);
      window.open(`https://web.whatsapp.com/send?text=${encodedText}`, '_blank');
    }).catch(err => {
      console.error('Failed to copy:', err);
      toast.error('Failed to copy to clipboard');
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

  // Fetch news (client-side)
  // Search for news by keyword (now handled by backend)
  const searchNewsForCompanies = async (companies: WatchlistCompany[]): Promise<any[]> => {
    const allArticles: any[] = [];

    for (const company of companies) {
      try {
        // Call backend search endpoint with company ID
        const response = await apiClient.post(
          `/api/v1/news/search?keyword=${encodeURIComponent(company.name)}&company_id=${company.id}`
        );

        if (response.data?.articles) {
          // Convert backend response format to expected format
          const articles = response.data.articles.map((article: any) => ({
            company_id: article.company_id,
            source: article.source,
            native_id: article.source === 'bursa' ? article.native_id : undefined,
            title: article.title,
            url: article.link || article.url,
            published_at: article.date || article.published_at,
            content: article.description || article.content,
            id: article.id  // Include the stored ID from backend
          }));
          allArticles.push(...articles);
        }
      } catch (err) {
        console.warn(`Error searching news for ${company.name}:`, err);
      }
    }

    return allArticles;
  };

  // Fetch user's watchlist and sync news
  useEffect(() => {
    if (hasFetched) return; // Prevent duplicate fetches

    const fetchWatchlist = async () => {
      try {
        setHasFetched(true);
        const response = await apiClient.get('/api/v1/watchlist/my-watchlist');
        const companies = response.data;

        const watchlistHasCompanies = companies.length > 0;
        setWatchlistEmpty(!watchlistHasCompanies);

        if (watchlistHasCompanies) {
          setWatchlistCompanies(companies);
        }

        // Step 1: Load existing news from database first (fast)
        const cachedNewsData = await newsApi.getFeed(50, watchlistHasCompanies);

        // Filter out Bursa announcements from display and deduplicate by ID
        const seenIds = new Set();
        const filteredCachedNews = cachedNewsData.filter(i => {
          if (i.type === 'bursa' || seenIds.has(i.id)) return false;
          seenIds.add(i.id);
          return true;
        });
        setUnifiedFeed(filteredCachedNews);

        // Calculate stats from cached data
        const cachedBursaCount = cachedNewsData.filter(i => i.type === 'bursa').length;
        const cachedStarCount = cachedNewsData.filter(i => i.type === 'star').length;
        const cachedNstCount = cachedNewsData.filter(i => i.type === 'nst').length;
        const cachedEdgeCount = cachedNewsData.filter(i => i.type === 'edge').length;

        setStats({
          bursa: cachedBursaCount,
          star: cachedStarCount,
          nst: cachedNstCount,
          edge: cachedEdgeCount,
          total: filteredCachedNews.length
        });

        setLoading(false); // Show cached data immediately

        // Step 2: Fetch fresh news in background
        if (watchlistHasCompanies) {
          // Fetch news from all sources (now Star & NST are fetched by backend)
          const [bursaArticles, newsArticles] = await Promise.all([
            fetchBursaAnnouncements(companies),
            searchNewsForCompanies(companies)  // Backend handles Star & NST
          ]);

          const allArticles = [...bursaArticles, ...newsArticles];

          // Deduplicate articles by native_id (same article can appear for multiple companies)
          const uniqueArticles = allArticles.reduce((acc, article) => {
            if (!acc.find((a: any) => a.native_id === article.native_id)) {
              acc.push(article);
            }
            return acc;
          }, [] as any[]);

          // Log sample of articles with content for debugging
          if (uniqueArticles.length > 0) {
            console.log(`[NEWS] Found ${allArticles.length} articles, ${uniqueArticles.length} unique after deduplication`);
            console.log('[NEWS] Sample articles with content:',
              uniqueArticles.slice(0, 2).map((a: any) => ({
                source: a.source,
                title: a.title.substring(0, 50),
                contentLength: a.content?.length || 0,
                contentPreview: a.content?.substring(0, 200)
              }))
            );
          }

          // Note: Articles from searchNewsForCompanies are already stored by backend
          // We just need to refresh the feed
          if (newsArticles.length > 0) {
            try {
              // Bursa articles still need to be stored via the old endpoint
              const bursaOnlyArticles = bursaArticles;
              if (bursaOnlyArticles.length > 0) {
                await apiClient.post('/api/v1/news/store-articles', bursaOnlyArticles);
              }

              // Step 3: Refresh feed with newly stored articles
              const updatedNewsData = await newsApi.getFeed(50, watchlistHasCompanies);

              // Filter out Bursa announcements from display and deduplicate by ID
              const seenIds2 = new Set();
              const filteredUpdatedNews = updatedNewsData.filter(i => {
                if (i.type === 'bursa' || seenIds2.has(i.id)) return false;
                seenIds2.add(i.id);
                return true;
              });
              setUnifiedFeed(filteredUpdatedNews);

              // Update stats with fresh data
              const updatedBursaCount = updatedNewsData.filter(i => i.type === 'bursa').length;
              const updatedStarCount = updatedNewsData.filter(i => i.type === 'star').length;
              const updatedNstCount = updatedNewsData.filter(i => i.type === 'nst').length;
              const updatedEdgeCount = updatedNewsData.filter(i => i.type === 'edge').length;

              setStats({
                bursa: updatedBursaCount,
                star: updatedStarCount,
                nst: updatedNstCount,
                edge: updatedEdgeCount,
                total: filteredUpdatedNews.length
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
  const getSourceBadge = (type: 'bursa' | 'star' | 'nst' | 'edge') => {
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
      case 'edge':
        return {
          label: 'THE EDGE',
          color: 'text-amber-500',
          bg: 'bg-amber-500/10',
          icon: Newspaper
        };
    }
  };

  // Stats data
  const statsData = [
    {
      label: 'Total Items',
      value: stats.total.toString(),
      change: 'News articles',
      changeColor: 'text-emerald-500',
      icon: FileText,
      iconColor: 'text-emerald-500',
      iconBg: 'bg-emerald-500/10',
      borderColor: 'border-emerald-500/20'
    },
    {
      label: 'News Sources',
      value: '3',
      change: `${stats.star} Star, ${stats.nst} NST, ${stats.edge} Edge`,
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

  // Filter feed based on active tab and selected company
  const filteredFeed = unifiedFeed.filter(item => {
    // Company filter
    if (selectedCompanyId !== 'all' && item.companyId !== selectedCompanyId) {
      return false;
    }

    // Sentiment filter
    if (activeTab === 'all') return true;
    if (activeTab === 'alerts') return item.sentiment?.label?.toLowerCase() === 'negative';
    return item.sentiment?.label?.toLowerCase() === activeTab;
  });

  // Calculate sentiment counts
  const sentimentCounts = {
    positive: unifiedFeed.filter(i => i.sentiment?.label?.toLowerCase() === 'positive').length,
    negative: unifiedFeed.filter(i => i.sentiment?.label?.toLowerCase() === 'negative').length,
    neutral: unifiedFeed.filter(i => i.sentiment?.label?.toLowerCase() === 'neutral').length,
  };

  // Calculate sentiment distribution from unified feed (excluding Bursa)
  const sentimentData = [
    { name: 'The Star', value: stats.star, color: '#3b82f6' }, // blue-500
    { name: 'NST', value: stats.nst, color: '#a855f7' },  // purple-500
    { name: 'The Edge', value: stats.edge, color: '#f59e0b' }  // amber-500
  ];

  // Intelligence Feed Component
  const feedComponent = (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-foreground">Market Intelligence Feed</h2>
        <span className="text-sm text-foreground-muted">
          {loading ? 'Loading...' : watchlistEmpty ? 'No companies in watchlist' : `${unifiedFeed.length} announcements • Real-time Bursa filings`}
        </span>
      </div>

      {/* Company Filter Dropdown */}
      {!watchlistEmpty && watchlistCompanies.length > 0 && (
        <div className="flex items-center gap-3">
          <label className="text-sm font-medium text-foreground-muted">Filter by company:</label>
          <select
            value={selectedCompanyId}
            onChange={(e) => setSelectedCompanyId(e.target.value)}
            className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-foreground text-sm font-medium focus:outline-none focus:ring-2 focus:ring-emerald-500/50 hover:bg-white/10 transition-colors cursor-pointer"
          >
            <option value="all" className="bg-gray-900 text-foreground">All Companies</option>
            {watchlistCompanies.map((company) => (
              <option key={company.id} value={company.id} className="bg-gray-900 text-foreground">
                {company.name} ({company.ticker})
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Sentiment Filter Tabs */}
      <div className="flex items-center gap-3 flex-wrap">
        <button
          onClick={() => setActiveTab('all')}
          className={`px-4 py-2 rounded-full text-sm font-semibold transition-all ${activeTab === 'all'
            ? 'bg-emerald-500 text-white'
            : 'bg-white/5 text-foreground-muted hover:bg-white/10'
            }`}
        >
          All
        </button>
        <button
          onClick={() => setActiveTab('alerts')}
          className={`px-4 py-2 rounded-full text-sm font-semibold transition-all flex items-center gap-2 ${activeTab === 'alerts'
            ? 'bg-red-500 text-white'
            : 'bg-white/5 text-foreground-muted hover:bg-white/10'
            }`}
        >
          <AlertTriangle size={16} />
          Alerts
          {sentimentCounts.negative > 0 && (
            <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${activeTab === 'alerts' ? 'bg-white/20' : 'bg-red-500/20 text-red-400'
              }`}>
              {sentimentCounts.negative}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('positive')}
          className={`px-4 py-2 rounded-full text-sm font-semibold transition-all ${activeTab === 'positive'
            ? 'bg-emerald-500 text-white'
            : 'bg-white/5 text-foreground-muted hover:bg-white/10'
            }`}
        >
          Positive
        </button>
        <button
          onClick={() => setActiveTab('negative')}
          className={`px-4 py-2 rounded-full text-sm font-semibold transition-all ${activeTab === 'negative'
            ? 'bg-red-500 text-white'
            : 'bg-white/5 text-foreground-muted hover:bg-white/10'
            }`}
        >
          Negative
        </button>
        <button
          onClick={() => setActiveTab('neutral')}
          className={`px-4 py-2 rounded-full text-sm font-semibold transition-all ${activeTab === 'neutral'
            ? 'bg-amber-500 text-white'
            : 'bg-white/5 text-foreground-muted hover:bg-white/10'
            }`}
        >
          Neutral
        </button>
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
          {filteredFeed.length === 0 ? (
            <GlassCard className="p-6">
              <p className="text-center text-foreground-muted">
                {unifiedFeed.length === 0
                  ? 'No news items found for your watched companies'
                  : `No ${activeTab === 'alerts' ? 'negative' : activeTab} sentiment items found`
                }
              </p>
            </GlassCard>
          ) : (
            filteredFeed.map((item) => {
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

              // Get hover border color based on sentiment
              const getHoverBorderColor = () => {
                if (!sentimentBadge) return 'hover:border-blue-500/50';

                switch (sentimentBadge.label) {
                  case 'positive':
                    return 'hover:border-emerald-500/70';
                  case 'negative':
                    return 'hover:border-red-500/70';
                  case 'neutral':
                    return 'hover:border-amber-500/70';
                  default:
                    return 'hover:border-blue-500/50';
                }
              };

              return (
                <GlassCard
                  key={item.id}
                  className={`p-6 relative overflow-hidden group transition-all ${getHoverBorderColor()}`}
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
                    <p className="text-foreground-secondary text-sm leading-relaxed mb-4">
                      {item.description.length > 200
                        ? `${item.description.substring(0, 200)}...`
                        : item.description}
                    </p>
                  )}

                  <div className="flex justify-end items-center gap-4">
                    <button
                      onClick={() => handleWhatsAppShare(item)}
                      className="text-emerald-500 hover:text-emerald-400 text-sm font-medium flex items-center gap-1.5 transition-colors opacity-90 hover:opacity-100"
                      title="Share via WhatsApp"
                    >
                      <WhatsAppIcon size={16} />
                      Share
                    </button>
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
  );

  // Source Distribution Chart Component
  const chartComponent = (
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
          News items from {stats.star} The Star, {stats.nst} NST, and {stats.edge} The Edge
        </p>
      </div>
    </GlassCard>
  );

  // Render dashboard based on persona
  const renderDashboard = () => {
    const layoutProps = { stats, feedComponent, chartComponent };

    switch (persona) {
      case 'INVESTOR':
        return <InvestorLayout {...layoutProps} />;
      case 'RELATIONSHIP_MANAGER':
        return <RelationshipManagerLayout {...layoutProps} />;
      case 'CREDIT_RISK':
        return <CreditRiskLayout {...layoutProps} />;
      case 'MARKET_ANALYST':
        return <MarketAnalystLayout {...layoutProps} />;
      default:
        return <InvestorLayout {...layoutProps} />;
    }
  };

  return renderDashboard();
}

export default function DashboardPage() {
  return (
    <ProtectedLayout>
      <DashboardContent />
    </ProtectedLayout>
  );
}
