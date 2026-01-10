'use client';

import ProtectedLayout from '@/components/layouts/ProtectedLayout';
import { useDocuments } from '@/hooks/useDocuments';
import { FileText, MessageCircle, Database, TrendingUp, Clock, Upload, ArrowRight } from 'lucide-react';
import Link from 'next/link';
import { formatDistanceToNow, subDays, isSameDay, format } from 'date-fns';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';

function DashboardContent() {
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

  const stats = [
    {
      label: 'Total Documents',
      value: totalDocuments,
      icon: FileText,
      color: 'from-blue-500 to-cyan-500',
      change: processingDocs > 0 ? `${processingDocs} processing` : 'All processed',
    },
    {
      label: 'Processed',
      value: processedDocs,
      icon: TrendingUp,
      color: 'from-green-500 to-emerald-500',
      change: `${((processedDocs / (totalDocuments || 1)) * 100).toFixed(0)}% complete`,
    },
    {
      label: 'Storage Used',
      value: formatBytes(totalStorage),
      icon: Database,
      color: 'from-purple-500 to-pink-500',
      change: `${totalDocuments} files`,
    },
    {
      label: 'Queries Today',
      value: 0,
      icon: MessageCircle,
      color: 'from-orange-500 to-red-500',
      change: 'No queries yet',
    },
  ];

  const quickActions = [
    {
      label: 'Upload Document',
      href: '/documents',
      icon: Upload,
      color: 'bg-blue-500 hover:bg-blue-600',
    },
    {
      label: 'Ask Question',
      href: '/chat',
      icon: MessageCircle,
      color: 'bg-purple-500 hover:bg-purple-600',
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            Dashboard
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400">
            Welcome back! Here's your overview.
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat, index) => (
            <div
              key={index}
              className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between mb-4">
                <div className={`p-3 bg-gradient-to-br ${stat.color} rounded-lg`}>
                  <stat.icon className="w-6 h-6 text-white" />
                </div>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                  {stat.label}
                </p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                  {stat.value}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-500">
                  {stat.change}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Analytics Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Upload Activity */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">Upload Activity</h3>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={activityData}>
                  <defs>
                    <linearGradient id="colorUploads" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#374151" opacity={0.1} />
                  <XAxis 
                      dataKey="name" 
                      stroke="#9CA3AF" 
                      fontSize={12}
                      tickLine={false}
                      axisLine={false}
                  />
                  <YAxis 
                      stroke="#9CA3AF" 
                      fontSize={12}
                      tickLine={false}
                      axisLine={false}
                      allowDecimals={false}
                  />
                  <Tooltip 
                      contentStyle={{ backgroundColor: '#1F2937', borderColor: '#374151', color: '#F3F4F6' }}
                      itemStyle={{ color: '#F3F4F6' }}
                      cursor={{ fill: 'transparent' }}
                  />
                  <Area type="monotone" dataKey="uploads" stroke="#3b82f6" fillOpacity={1} fill="url(#colorUploads)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Status Distribution */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">Document Status</h3>
            <div className="h-64 w-full">
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
                      >
                      {statusData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                      </Pie>
                      <Tooltip 
                          contentStyle={{ backgroundColor: '#1F2937', borderColor: '#374151', color: '#F3F4F6' }}
                          itemStyle={{ color: '#F3F4F6' }}
                      />
                      <Legend />
                  </PieChart>
                  </ResponsiveContainer>
              ) : (
                  <div className="h-full flex items-center justify-center text-gray-500">
                      No data available
                  </div>
              )}
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mb-8">
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
            Quick Actions
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {quickActions.map((action, index) => (
              <Link key={index} href={action.href}>
                <div
                  className={`${action.color} text-white rounded-xl p-6 flex items-center justify-between cursor-pointer transition-all hover:scale-105 shadow-lg`}
                >
                  <div className="flex items-center space-x-4">
                    <div className="p-3 bg-white/20 rounded-lg">
                      <action.icon className="w-6 h-6" />
                    </div>
                    <span className="text-lg font-semibold">{action.label}</span>
                  </div>
                  <ArrowRight className="w-6 h-6" />
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div>
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
            Recent Documents
          </h2>
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              </div>
            ) : documents.length === 0 ? (
              <div className="text-center py-12">
                <FileText className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-600 dark:text-gray-400">No documents yet</p>
                <Link href="/documents">
                  <button className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors">
                    Upload Your First Document
                  </button>
                </Link>
              </div>
            ) : (
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {documents.slice(0, 5).map((doc) => (
                  <div
                    key={doc.id}
                    className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg">
                          <FileText className="w-5 h-5 text-white" />
                        </div>
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">
                            {doc.filename}
                          </p>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            {formatDistanceToNow(new Date(doc.uploadDate), {
                              addSuffix: true,
                            })}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span
                          className={`px-3 py-1 text-xs font-medium rounded-full ${
                            doc.status === 'PROCESSED'
                              ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                              : doc.status === 'PROCESSING'
                              ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                              : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300'
                          }`}
                        >
                          {doc.status}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
            {documents.length > 5 && (
              <div className="px-6 py-4 bg-gray-50 dark:bg-gray-700/30 text-center">
                <Link href="/documents">
                  <span className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium cursor-pointer">
                    View all {documents.length} documents →
                  </span>
                </Link>
              </div>
            )}
          </div>
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
