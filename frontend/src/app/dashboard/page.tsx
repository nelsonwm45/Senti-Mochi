'use client';

import { useRouter } from 'next/navigation';
import ProtectedLayout from '@/components/layouts/ProtectedLayout';
import { 
  FileText, 
  AlertTriangle,
  Clock,
  ArrowRight,
  ExternalLink,
  TrendingUp,
  Minus,
  TrendingDown
} from 'lucide-react';
import { GlassCard } from '@/components/ui/GlassCard';
import {
  PieChart, Pie, Cell, Legend, ResponsiveContainer, Tooltip
} from 'recharts';

function DashboardContent() {
  const router = useRouter();

  // Mock Data for Stats
  const stats = [
    {
      label: 'Filings Today',
      value: '24',
      change: '+8 from yesterday',
      changeColor: 'text-emerald-500',
      icon: FileText,
      iconColor: 'text-emerald-500',
      iconBg: 'bg-emerald-500/10',
      borderColor: 'border-emerald-500/20'
    },
    {
      label: 'Active Alerts',
      value: '3',
      change: '',
      changeColor: '',
      icon: AlertTriangle,
      iconColor: 'text-red-500',
      iconBg: 'bg-red-500/10',
      borderColor: 'border-red-500/20'
    },
    {
      label: 'Last Updated',
      value: '2 min ago',
      change: '',
      changeColor: '',
      icon: Clock,
      iconColor: 'text-emerald-500',
      iconBg: 'bg-emerald-500/10',
      borderColor: 'border-emerald-500/20'
    }
  ];

  // Mock Data for Intelligence Feed
  const feedItems = [
    {
      id: 1,
      company: 'Petronas Chemicals Group',
      ticker: 'PCHEM',
      type: 'QUARTERLY REPORT',
      sentiment: 'Positive',
      time: '15 Jan, 05:30 pm',
      description: 'Q3 2024 results exceeded expectations with 15% YoY revenue growth. Strong petrochemical margins and operational efficiency improvements drove profitability.',
      sentimentColor: 'text-emerald-500',
      sentimentBg: 'bg-emerald-500/10',
      sentimentIcon: TrendingUp
    },
    {
      id: 2,
      company: 'CIMB Group Holdings',
      ticker: 'CIMB',
      type: 'DIRECTOR CHANGE',
      sentiment: 'Neutral',
      time: '15 Jan, 04:45 pm',
      description: 'Appointment of new Independent Non-Executive Director effective February 2024. No material impact on current strategic direction expected.',
      sentimentColor: 'text-yellow-500',
      sentimentBg: 'bg-yellow-500/10',
      sentimentIcon: Minus
    },
    {
      id: 3,
      company: 'Top Glove Corporation',
      ticker: 'TOPGLOV',
      type: 'PROFIT WARNING',
      sentiment: 'Negative',
      time: '15 Jan, 12:20 am',
      description: 'Revenue declined 23% as glove demand normalizes post-pandemic. Management initiated cost restructuring program to improve margins.',
      sentimentColor: 'text-red-500',
      sentimentBg: 'bg-red-500/10',
      sentimentIcon: TrendingDown,
      isAlert: true
    }
  ];

  // Mock Data for Sentiment Distribution
  const sentimentData = [
    { name: 'Positive', value: 35, color: '#10b981' }, // emerald-500
    { name: 'Neutral', value: 45, color: '#eab308' }, // yellow-500
    { name: 'Negative', value: 20, color: '#ef4444' }  // red-500
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
        {stats.map((stat, index) => (
          <GlassCard key={index} className={`p-6 flex items-center gap-4 ${stat.borderColor} border`}>
            <div className={`p-3 rounded-xl ${stat.iconBg}`}>
              <stat.icon size={24} className={stat.iconColor} />
            </div>
            <div>
              <p className="text-sm text-foreground-muted">{stat.label}</p>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-foreground">{stat.value}</span>
                {stat.change && (
                  <span className={`text-sm ${stat.changeColor} font-medium`}>{stat.change}</span>
                )}
              </div>
            </div>
          </GlassCard>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Intelligence Feed */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-foreground">Intelligence Feed</h2>
            <span className="text-sm text-foreground-muted">Showing 6 announcements from watchlist</span>
          </div>

          <div className="space-y-4">
            {feedItems.map((item) => (
              <GlassCard 
                key={item.id} 
                className={`p-6 relative overflow-hidden group ${item.isAlert ? 'border-red-500/50' : ''}`}
              >
                {item.isAlert && (
                   <div className="absolute top-0 right-0 bg-red-500 text-white text-xs font-bold px-3 py-1 rounded-bl-lg flex items-center gap-1">
                     <AlertTriangle size={12} /> ALERT
                   </div>
                )}
                
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <div className="flex items-baseline gap-2 mb-2">
                      <h3 className="text-lg font-bold text-foreground">{item.company}</h3>
                      <span className="text-sm text-foreground-muted">{item.ticker}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-semibold px-2 py-1 rounded bg-white/5 text-foreground-muted uppercase tracking-wider">
                        {item.type}
                      </span>
                      <div className={`flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full ${item.sentimentBg} ${item.sentimentColor}`}>
                        <item.sentimentIcon size={12} />
                        {item.sentiment}
                      </div>
                    </div>
                  </div>
                  <span className="text-sm text-foreground-muted flex items-center gap-1 mt-8 md:mt-0">
                     <Clock size={14} /> {item.time}
                  </span>
                </div>

                <p className="text-foreground-secondary text-sm leading-relaxed mb-4">
                  {item.description}
                </p>

                <div className="flex justify-end">
                  <button className="text-emerald-500 hover:text-emerald-400 text-sm font-medium flex items-center gap-1 transition-colors">
                    View Source <ExternalLink size={14} />
                  </button>
                </div>
              </GlassCard>
            ))}
          </div>
        </div>

        {/* Sidebar: Sentiment Distribution */}
        <div>
          <GlassCard className="p-6 h-fit sticky top-6">
            <h3 className="text-lg font-semibold text-foreground mb-6">Sentiment Distribution</h3>
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
                 Based on analysis of 145 recent filings
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
