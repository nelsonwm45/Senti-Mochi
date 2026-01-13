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

  // Fetch user's watchlist
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

        // Fetch news from backend (persisted data)
        // If watchlist is empty, show all news. Otherwise, show only watchlist news.
        const newsData = await newsApi.getFeed(50, watchlistHasCompanies);
        
        setUnifiedFeed(newsData);
        
        // Calculate stats from the response
        const bursaCount = newsData.filter(i => i.type === 'bursa').length;
        const starCount = newsData.filter(i => i.type === 'star').length;
        const nstCount = newsData.filter(i => i.type === 'nst').length;
        
        setStats({
          bursa: bursaCount,
          star: starCount,
          nst: nstCount,
          total: newsData.length
        });

      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch watchlist');
        console.error('Error fetching watchlist:', err);
      } finally {
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
