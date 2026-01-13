'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ProtectedLayout from '@/components/layouts/ProtectedLayout';
import apiClient from '@/lib/apiClient';
import { bursaCompanies } from '@/lib/bursaCompanies';
import {
  FileText,
  AlertTriangle,
  Clock,
  ArrowRight,
  ExternalLink,
  TrendingUp,
  Minus,
  TrendingDown,
  Newspaper,
  Download
} from 'lucide-react';
import { GlassCard } from '@/components/ui/GlassCard';
import {
  PieChart, Pie, Cell, Legend, ResponsiveContainer, Tooltip
} from 'recharts';

interface ParsedAnnouncement {
  id: number;
  disclosureId: number;
  date: string;
  dateRaw: string;
  companyName: string;
  companyLink?: string;
  companyCode?: string;
  title: string;
  announcementLink?: string;
}

interface ApiResponse {
  data?: Array<[number, string, string, string]>;
  [key: string]: any;
}

interface StarArticle {
  _id: number;
  title: string;
  link: string;
  description: string;
  pubdate: string;
  pubdateunix: number;
  image?: string;
  feedname: string;
}

interface NSTArticle {
  nid: number;
  title: string;
  created: number;
  url: string;
  internal_url: string;
  field_article_topic?: {
    tid: number;
    name: string;
  };
  field_article_lead?: string;
}

interface WatchlistCompany {
  id: string;
  name: string;
  ticker: string;
  sector?: string;
  sub_sector?: string;
  website_url?: string;
}

interface UnifiedFeedItem {
  id: string;
  type: 'bursa' | 'star' | 'nst';
  title: string;
  link: string;
  date: string;
  timestamp: number;
  disclosureId?: number;
  company?: string;
  companyCode?: string;
  description?: string;
  source: string;
}

// Utility function to decode HTML entities
const decodeHtml = (html: string): string => {
  const txt = document.createElement('textarea');
  txt.innerHTML = html;
  return txt.value;
};

// Utility function to extract text and link from HTML string
const parseHtmlLink = (htmlString: string): { text: string; link?: string } => {
  const decoded = decodeHtml(htmlString);

  // Try to extract link from anchor tag
  const linkMatch = decoded.match(/<a[^>]+href=['"]([^'"]+)['"][^>]*>(.*?)<\/a>/i);
  if (linkMatch) {
    return {
      text: linkMatch[2].replace(/<[^>]*>/g, '').trim(),
      link: linkMatch[1]
    };
  }

  // If no link, just extract text and remove HTML tags
  const text = decoded.replace(/<[^>]*>/g, '').trim();
  return { text };
};

// Parse announcement array into structured object
const parseAnnouncement = (announcementArray: [number, string, string, string]): ParsedAnnouncement => {
  const [id, dateHtml, companyHtml, titleHtml] = announcementArray;

  // Parse date (remove HTML tags and clean up)
  const dateParsed = parseHtmlLink(dateHtml);
  const dateText = dateParsed.text.replace(/\s+/g, ' ').trim();

  // Parse company info
  const companyParsed = parseHtmlLink(companyHtml);
  const companyLink = companyParsed.link;
  // Extract company code from link if available
  const companyCodeMatch = companyLink?.match(/stock_code=(\d+)/);
  const companyCode = companyCodeMatch ? companyCodeMatch[1] : undefined;

  // Parse title
  const titleParsed = parseHtmlLink(titleHtml);

  // Extract disclosure ID (ann_id) from announcement link
  const disclosureIdMatch = titleParsed.link?.match(/ann_id=(\d+)/);
  const disclosureId = disclosureIdMatch ? parseInt(disclosureIdMatch[1], 10) : 0;

  return {
    id,
    disclosureId,
    date: dateText,
    dateRaw: dateHtml,
    companyName: companyParsed.text,
    companyLink: companyLink ? `https://www.bursamalaysia.com${companyLink}` : undefined,
    companyCode,
    title: titleParsed.text,
    announcementLink: titleParsed.link ? `https://www.bursamalaysia.com${titleParsed.link}` : undefined
  };
};

function DashboardContent() {
  const router = useRouter();
  const [unifiedFeed, setUnifiedFeed] = useState<UnifiedFeedItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [watchlistEmpty, setWatchlistEmpty] = useState(false);
  const [watchlistCompanies, setWatchlistCompanies] = useState<WatchlistCompany[]>([]);
  const [downloadingIds, setDownloadingIds] = useState<Set<string>>(new Set());
  const [downloadError, setDownloadError] = useState<string | null>(null);
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

        if (companies.length === 0) {
          setWatchlistEmpty(true);
          setLoading(false);
          return;
        }

        setWatchlistCompanies(companies);

        // Now fetch all news for these companies
        const [bursaResponse, starResponse, nstResponse] = await Promise.all([
          fetchBursaAnnouncements(companies),
          fetchStarNews(companies),
          fetchNSTNews(companies)
        ]);

        // Combine and sort all items by timestamp
        const combinedFeed = [
          ...bursaResponse,
          ...starResponse,
          ...nstResponse
        ].sort((a, b) => b.timestamp - a.timestamp);

        setUnifiedFeed(combinedFeed);
        setStats({
          bursa: bursaResponse.length,
          star: starResponse.length,
          nst: nstResponse.length,
          total: combinedFeed.length
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

  // Fetch Bursa Malaysia announcements for multiple companies
  const fetchBursaAnnouncements = async (companies: WatchlistCompany[]): Promise<UnifiedFeedItem[]> => {
    try {
      const allAnnouncements: UnifiedFeedItem[] = [];

      for (const company of companies) {
        // Find the Bursa ticker in bursaCompanies and extract the numeric code (remove .KL)
        const bursaCompany = bursaCompanies.find(bc =>
          bc.name.toLowerCase().includes(company.name.toLowerCase()) ||
          bc.ticker.split('.')[0] === company.ticker?.split('.')[0]
        );

        if (!bursaCompany) {
          console.warn(`No Bursa company found for ${company.name}`);
          continue;
        }

        // Extract numeric ID from ticker (e.g., "1155.KL" -> "1155")
        const bursaCode = bursaCompany.ticker.split('.')[0];
        const url = `https://www.bursamalaysia.com/api/v1/announcements/search?ann_type=company&company=${bursaCode}&cat=AR,ARCO&per_page=5&page=1`;

        try {
          const response = await fetch(url, {
            method: 'GET',
            headers: {
              'Accept': 'application/json',
            },
          });

          if (!response.ok) {
            console.warn(`Bursa API error for ${company.name}: ${response.status}`);
            continue;
          }

          const jsonData: ApiResponse = await response.json();
          const parsedAnnouncements = jsonData.data
            ? jsonData.data.map(parseAnnouncement)
            : [];

          allAnnouncements.push(...parsedAnnouncements.slice(0, 5).map(ann => ({
            id: `bursa-${bursaCode}-${ann.id}`,
            type: 'bursa' as const,
            title: ann.title,
            link: ann.announcementLink || '',
            date: ann.date,
            timestamp: parseDateToTimestamp(ann.date),
            disclosureId: ann.disclosureId,
            company: ann.companyName,
            companyCode: ann.companyCode,
            source: 'Bursa Malaysia'
          })));
        } catch (err) {
          console.error(`Error fetching Bursa announcements for ${company.name}:`, err);
          continue;
        }
      }

      return allAnnouncements;
    } catch (err) {
      console.error('Error fetching Bursa announcements:', err);
      return [];
    }
  };

  // Fetch The Star news for multiple companies
  const fetchStarNews = async (companies: WatchlistCompany[]): Promise<UnifiedFeedItem[]> => {
    try {
      const allArticles: UnifiedFeedItem[] = [];

      for (const company of companies) {
        const searchQuery = company.name;
        const encodedQuery = encodeURIComponent(searchQuery);
        const url = `https://api.queryly.com/json.aspx?queryly_key=6ddd278bf17648ac&query=${encodedQuery}&endindex=0&batchsize=5&showfaceted=true&extendeddatafields=paywalltype,isexclusive,kicker,kickerurl,summary,sponsor&timezoneoffset=-450`;

        try {
          const response = await fetch(url, {
            method: 'GET',
            headers: {
              'Accept': 'application/json',
            },
          });

          if (!response.ok) {
            console.warn(`Star API error for ${company.name}: ${response.status}`);
            continue;
          }

          const text = await response.text();
          let jsonData: any;

          // Handle JSONP response
          if (text.includes('resultcallback')) {
            const jsonMatch = text.match(/resultcallback\s*\(\s*({[\s\S]*})\s*\)/);
            if (jsonMatch && jsonMatch[1]) {
              jsonData = JSON.parse(jsonMatch[1]);
            } else {
              console.warn(`Unable to parse JSONP response for ${company.name}`);
              continue;
            }
          } else {
            jsonData = JSON.parse(text);
          }

          const articles: StarArticle[] = jsonData.items || [];

          allArticles.push(...articles.map(article => ({
            id: `star-${company.ticker}-${article._id}`,
            type: 'star' as const,
            title: article.title,
            link: article.link,
            date: article.pubdate,
            timestamp: article.pubdateunix,
            description: article.description,
            company: company.name,
            source: 'The Star'
          })));
        } catch (err) {
          console.error(`Error fetching Star news for ${company.name}:`, err);
          continue;
        }
      }

      return allArticles;
    } catch (err) {
      console.error('Error fetching Star news:', err);
      return [];
    }
  };

  // Fetch NST news for multiple companies
  const fetchNSTNews = async (companies: WatchlistCompany[]): Promise<UnifiedFeedItem[]> => {
    try {
      const allArticles: UnifiedFeedItem[] = [];

      for (const company of companies) {
        const searchQuery = company.name;
        const url = `/api/nst?keywords=${encodeURIComponent(searchQuery)}&category=&sort=DESC&page_size=5&page=0`;

        try {
          const response = await fetch(url, {
            method: 'GET',
            headers: {
              'Accept': 'application/json',
            },
          });

          if (!response.ok) {
            console.warn(`NST API error for ${company.name}: ${response.status}`);
            continue;
          }

          const jsonData = await response.json();
          const articles: NSTArticle[] = jsonData.data || [];

          allArticles.push(...articles.slice(0, 5).map(article => ({
            id: `nst-${company.ticker}-${article.nid}`,
            type: 'nst' as const,
            title: article.title,
            link: article.url,
            date: formatNSTDate(article.created),
            timestamp: article.created,
            description: article.field_article_lead,
            company: company.name,
            source: 'NST'
          })));
        } catch (err) {
          console.error(`Error fetching NST news for ${company.name}:`, err);
          continue;
        }
      }

      return allArticles;
    } catch (err) {
      console.error('Error fetching NST news:', err);
      return [];
    }
  };

  // Helper function to parse date string to timestamp
  const parseDateToTimestamp = (dateStr: string): number => {
    try {
      // Handle Bursa date format: "15 Jan 2026, 05:30 pm"
      const date = new Date(dateStr);
      return date.getTime() / 1000;
    } catch {
      return Date.now() / 1000;
    }
  };

  // Helper function to format NST date
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

  // Handle Bursa PDF download
  const handleDownloadBursaPDF = async (item: UnifiedFeedItem) => {
    const disclosureId = item.disclosureId;

    if (!disclosureId) {
      alert('No disclosure ID found for this announcement');
      return;
    }

    const downloadId = `bursa-${disclosureId}`;

    try {
      setDownloadingIds(prev => new Set(prev).add(downloadId));
      setDownloadError(null);

      // Fetch available PDFs for this disclosure
      const disclosureResponse = await apiClient.get('/api/v1/bursa/fetch-disclosure', {
        params: { disclosure_id: String(disclosureId) }
      });

      const pdfs = disclosureResponse.data.pdfs || [];

      // Pick the first PDF (Bursa pages usually have a single primary PDF)
      const targetPDF = pdfs[0];

      if (!targetPDF) {
        throw new Error('PDF not found in disclosure');
      }

      // Download the PDF via the backend scraper
      const downloadResponse = await apiClient.post('/api/v1/bursa/download-pdf', {
        disclosure_id: String(disclosureId),
        pdf_url: targetPDF.url,
        filename: targetPDF.name,
        company_name: item.company || 'unknown'
      });

      if (downloadResponse.data.success) {
        setDownloadError(null);
        alert(`✅ Downloaded: ${targetPDF.name}\nSaved to Bursa downloads folder`);
      } else {
        throw new Error(downloadResponse.data.message || 'Download failed');
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to download PDF';
      setDownloadError(errorMsg);
      alert(`❌ Download failed: ${errorMsg}`);
      console.error('Download error:', err);
    } finally {
      setDownloadingIds(prev => {
        const updated = new Set(prev);
        updated.delete(downloadId);
        return updated;
      });
    }
  };

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

                      <div className="flex justify-end gap-3">
                        {item.type === 'bursa' && item.disclosureId && (
                          <button
                            onClick={() => handleDownloadBursaPDF(item)}
                            disabled={downloadingIds.has(`bursa-${item.disclosureId}`)}
                            className="text-blue-500 hover:text-blue-400 text-sm font-medium flex items-center gap-1 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {downloadingIds.has(`bursa-${item.disclosureId}`) ? (
                              <>
                                <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-500"></div>
                                Downloading...
                              </>
                            ) : (
                              <>
                                <Download size={14} />
                                Download PDF
                              </>
                            )}
                          </button>
                        )}
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
