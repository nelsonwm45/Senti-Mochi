'use client';

import { useRouter } from 'next/navigation';
import ProtectedLayout from '@/components/layouts/ProtectedLayout';
import { useDocuments } from '@/hooks/useDocuments';
import { 
  FileText, 
  MessageCircle, 
  Database, 
  TrendingUp, 
  Upload, 
  ArrowRight,
  Plus,
  Loader2
} from 'lucide-react';
import Link from 'next/link';
import { formatDistanceToNow, subDays, isSameDay, format } from 'date-fns';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';
import { motion } from 'framer-motion';

import { GlassCard } from '@/components/ui/GlassCard';
import { GlassButton } from '@/components/ui/GlassButton';
import { FAB } from '@/components/layout/FAB';
import { MarketTicker } from '@/components/dashboard/MarketTicker';
import { PortfolioChart } from '@/components/dashboard/PortfolioChart';
import { HighImpactNews } from '@/components/dashboard/HighImpactNews';

function DashboardContent() {
  const router = useRouter();
  const { data: documentsData, isLoading } = useDocuments();
  const documents = documentsData?.documents || [];

  // Calculate stats
  const totalDocuments = documents.length;
  const processedDocs = documents.filter((d) => d.status === 'PROCESSED').length;
  const processingDocs = documents.filter((d) => d.status === 'PROCESSING').length;
  const failedDocs = documents.filter((d) => d.status === 'FAILED').length;
  const totalStorage = documents.reduce((acc, d) => acc + d.fileSize, 0);

  // Activity Data (Last 7 days)
  const activityData = Array.from({ length: 7 }).map((_, i) => {
    const date = subDays(new Date(), 6 - i);
    const count = documents.filter(d => 
      isSameDay(new Date(d.uploadDate), date)
    ).length;
    return {
      name: format(date, 'MMM dd'),
      uploads: count,
    };
  });

  // Status Distribution
  const statusData = [
    { name: 'Processed', value: processedDocs, color: '#10b981' },
    { name: 'Processing', value: processingDocs, color: '#3b82f6' },
    { name: 'Failed', value: failedDocs, color: '#ef4444' },
  ].filter(d => d.value > 0);

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const currentDate = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  const stats = [
    {
      label: 'Total Documents',
      value: totalDocuments,
      icon: FileText,
      gradient: 'bg-gradient-to-br from-blue-500 to-cyan-500',
      change: processingDocs > 0 ? `${processingDocs} processing` : 'All processed',
    },
    {
      label: 'Processed',
      value: processedDocs,
      icon: TrendingUp,
      gradient: 'bg-gradient-to-br from-green-500 to-emerald-500',
      change: `${totalDocuments ? ((processedDocs / totalDocuments) * 100).toFixed(0) : 0}% complete`,
    },
    {
      label: 'Storage Used',
      value: formatBytes(totalStorage),
      icon: Database,
      gradient: 'bg-gradient-to-br from-purple-500 to-pink-500',
      change: `${totalDocuments} files`,
    },
    {
      label: 'Queries Today',
      value: 0,
      icon: MessageCircle,
      gradient: 'bg-gradient-to-br from-orange-500 to-red-500',
      change: 'No queries yet',
    },
  ];

  const quickActions = [
    {
      label: 'Upload Document',
      description: 'Add new files to your knowledge base',
      href: '/documents',
      icon: Upload,
      gradient: 'bg-gradient-to-br from-blue-500/20 to-blue-600/20 text-blue-500',
    },
    {
      label: 'Start New Chat',
      description: 'Ask questions about your documents',
      href: '/chat',
      icon: MessageCircle,
      gradient: 'bg-gradient-to-br from-purple-500/20 to-purple-600/20 text-purple-500',
    },
  ];

  const fabActions = [
    {
      icon: <MessageCircle size={20} />,
      label: 'New Chat',
      onClick: () => router.push('/chat'),
    },
    {
      icon: <Upload size={20} />,
      label: 'Upload File',
      onClick: () => router.push('/documents'),
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header & Ticker */}
      <div className="-mx-4 md:-mx-8 -mt-8 mb-8">
         <MarketTicker />
      </div>

      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-accent mb-1">{currentDate}</p>
          <h1 className="text-3xl md:text-4xl font-bold">
            <span className="gradient-text">Welcome back!</span>
          </h1>
          <p className="text-foreground-muted mt-2">
            Market overview and document insights.
          </p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <GlassCard key={index} className="p-6 relative overflow-hidden group">
            <div className="relative z-10">
              <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-xl ${stat.gradient} text-white shadow-lg`}>
                  <stat.icon size={24} />
                </div>
                {/* Decorative background element */}
                <div className={`absolute -right-6 -top-6 w-24 h-24 rounded-full ${stat.gradient} opacity-10 group-hover:opacity-20 transition-opacity blur-2xl`} />
              </div>
              <div>
                <p className="text-sm font-medium text-foreground-secondary mb-1">
                  {stat.label}
                </p>
                <div className="flex items-baseline gap-2">
                  <h3 className="text-2xl font-bold text-foreground">
                    {stat.value}
                  </h3>
                </div>
                <p className="text-xs text-foreground-muted mt-1">
                  {stat.change}
                </p>
              </div>
            </div>
          </GlassCard>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content Column (Charts) */}
        <div className="lg:col-span-2 space-y-8">
          {/* Charts Row */}
          <div className="grid grid-cols-1 gap-8">
            <PortfolioChart />
            
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
               <HighImpactNews />
               
               {/* Upload Activity (Smaller/Secondary) */}
               <GlassCard className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-lg font-semibold text-foreground">Upload Activity</h3>
                </div>
                <div className="h-[250px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={activityData}>
                      <defs>
                        <linearGradient id="colorUploads" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.1)" />
                      <XAxis 
                        dataKey="name" 
                        stroke="#94a3b8" 
                        fontSize={10}
                        tickLine={false}
                        axisLine={false}
                        dy={10}
                      />
                      <YAxis 
                        stroke="#94a3b8" 
                        fontSize={10}
                        tickLine={false}
                        axisLine={false}
                        allowDecimals={false}
                        dx={-10}
                      />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: 'rgba(17, 24, 39, 0.8)', 
                          borderColor: 'rgba(255, 255, 255, 0.1)', 
                          backdropFilter: 'blur(12px)',
                          borderRadius: '12px',
                          color: '#fff' 
                        }}
                        itemStyle={{ color: '#e2e8f0' }}
                        cursor={{ stroke: 'rgba(139, 92, 246, 0.5)', strokeWidth: 2 }}
                      />
                      <Area 
                        type="monotone" 
                        dataKey="uploads" 
                        stroke="#8b5cf6" 
                        strokeWidth={3}
                        fillOpacity={1} 
                        fill="url(#colorUploads)" 
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </GlassCard>
            </div>
          </div>

          {/* Quick Actions */}
          <div>
            <h3 className="text-lg font-semibold text-foreground mb-4">Quick Actions</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {quickActions.map((action, index) => (
                <Link key={index} href={action.href}>
                  <GlassCard 
                    variant="interactive"
                    className="p-6 h-full flex items-center justify-between group"
                  >
                    <div className="flex items-center gap-4">
                      <div className={`p-3 rounded-xl ${action.gradient}`}>
                        <action.icon size={24} />
                      </div>
                      <div>
                        <h4 className="font-semibold text-foreground group-hover:text-accent transition-colors">
                          {action.label}
                        </h4>
                        <p className="text-sm text-foreground-muted">
                          {action.description}
                        </p>
                      </div>
                    </div>
                    <ArrowRight className="w-5 h-5 text-foreground-muted group-hover:text-accent group-hover:translate-x-1 transition-all" />
                  </GlassCard>
                </Link>
              ))}
            </div>
          </div>
        </div>

        {/* Sidebar Column */}
        <div className="space-y-8">
          {/* Status Distribution */}
          <GlassCard className="p-6">
            <h3 className="text-lg font-semibold text-foreground mb-6">Document Status</h3>
            <div className="h-[250px] w-full">
              {statusData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={statusData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                      stroke="none"
                    >
                      {statusData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'rgba(17, 24, 39, 0.8)', 
                        borderColor: 'rgba(255, 255, 255, 0.1)', 
                        backdropFilter: 'blur(12px)',
                        borderRadius: '12px',
                        color: '#fff' 
                      }}
                      itemStyle={{ color: '#e2e8f0' }}
                    />
                    <Legend wrapperStyle={{ paddingTop: '20px' }} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-foreground-muted">
                  <Database className="w-8 h-8 mb-2 opacity-50" />
                  <p className="text-sm">No documents yet</p>
                </div>
              )}
            </div>
          </GlassCard>

          {/* Recent Activity */}
          <GlassCard className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-foreground">Recent Activity</h3>
              <Link href="/documents">
                 <span className="text-xs text-accent hover:text-accent-light cursor-pointer font-medium">View All</span>
              </Link>
            </div>
            
            <div className="space-y-4">
              {isLoading ? (
                <div className="flex justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-accent" />
                </div>
              ) : documents.length === 0 ? (
                <div className="text-center py-8 text-foreground-muted">
                  <p className="text-sm">No recent activity</p>
                </div>
              ) : (
                documents.slice(0, 5).map((doc) => (
                  <div key={doc.id} className="flex items-start gap-3 p-3 rounded-xl hover:bg-white/5 transition-colors">
                    <div className="p-2 bg-accent/10 rounded-lg text-accent mt-0.5">
                      <FileText size={16} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-foreground truncate">
                        {doc.filename}
                      </p>
                      <p className="text-xs text-foreground-muted">
                        {formatDistanceToNow(new Date(doc.uploadDate), { addSuffix: true })}
                      </p>
                    </div>
                    <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${
                      doc.status === 'PROCESSED' ? 'bg-emerald-500' :
                      doc.status === 'PROCESSING' ? 'bg-blue-500' : 'bg-red-500'
                    }`} />
                  </div>
                ))
              )}
            </div>
          </GlassCard>
        </div>
      </div>

      {/* FAB */}
      <FAB actions={fabActions} />
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
