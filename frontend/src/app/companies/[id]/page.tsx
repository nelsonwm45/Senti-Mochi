'use client';

import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { companyApi, CompanyOverview } from '@/lib/api/company';
import ProtectedLayout from '@/components/layouts/ProtectedLayout';
import { GlassCard } from '@/components/ui/GlassCard';
import { Loader2, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { OverviewTab } from '@/components/company/OverviewTab';
import { FinancialsTab } from '@/components/company/FinancialsTab';
import { NewsTab } from '@/components/company/NewsTab';
// import { ChatInterface } from '@/components/copilot/ChatInterface'; // We'll add this later or in a separate tab

export default function CompanyPage() {
  const params = useParams();
  const id = params?.id as string;
  
  const [data, setData] = useState<CompanyOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'overview' | 'financials' | 'news'>('overview');

  useEffect(() => {
    if (!id) return;
    async function fetchData() {
      try {
        const res = await companyApi.getOverview(id);
        setData(res);
      } catch (err: any) {
        console.error(err);
        // For MVP demo, if 404, maybe show mock data?
        // But let's handle error gracefully
        setError('Failed to load company data.');
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [id]);

  if (loading) {
    return (
      <ProtectedLayout>
        <div className="flex h-full items-center justify-center">
          <Loader2 className="animate-spin text-accent w-8 h-8" />
        </div>
      </ProtectedLayout>
    );
  }

  if (error || !data) {
    return (
      <ProtectedLayout>
        <div className="flex flex-col items-center justify-center h-full gap-4">
          <p className="text-red-500">{error || 'Company not found'}</p>
          <Link href="/dashboard" className="text-accent hover:underline flex items-center gap-2">
            <ArrowLeft size={16} /> Back to Dashboard
          </Link>
        </div>
      </ProtectedLayout>
    );
  }

  return (
    <ProtectedLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
           <Link href="/dashboard" className="p-2 hover:bg-white/5 rounded-full transition-colors">
              <ArrowLeft className="text-foreground-muted" />
           </Link>
           <div>
             <h1 className="text-3xl font-bold text-foreground">{data.name}</h1>
             <p className="text-foreground-muted flex items-center gap-2">
               <span className="font-mono bg-accent/10 text-accent px-2 py-0.5 rounded text-sm">{data.ticker}</span>
               <span>•</span>
               <span>{data.sector}</span>
             </p>
           </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-4 border-b border-white/10">
           {['overview', 'financials', 'news'].map((tab) => (
             <button
               key={tab}
               onClick={() => setActiveTab(tab as any)}
               className={`pb-3 px-4 text-sm font-medium transition-colors relative ${
                 activeTab === tab ? 'text-accent' : 'text-foreground-muted hover:text-foreground'
               }`}
             >
               {tab.charAt(0).toUpperCase() + tab.slice(1)}
               {activeTab === tab && (
                 <div className="absolute bottom-0 left-0 w-full h-0.5 bg-accent shadow-[0_0_10px_rgba(139,92,246,0.5)]" />
               )}
             </button>
           ))}
        </div>

        {/* Content */}
        <div className="min-h-[500px]">
           {activeTab === 'overview' && <OverviewTab company={data} filings={data.recent_filings} />}
           {activeTab === 'financials' && <FinancialsTab ratios={data.financial_ratios} />}
           {activeTab === 'news' && <NewsTab news={data.recent_news} />}
        </div>
      </div>
    </ProtectedLayout>
  );
}
