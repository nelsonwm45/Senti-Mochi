'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Scale, AlertTriangle, X, Loader2, Clock } from 'lucide-react';
import { GlassCard } from '@/components/ui/GlassCard';
import { cn } from '@/lib/utils';
import {
  analysisApi,
  AnalysisReport,
  getRoleBasedInsight,
  getCitationRegistry,
  SourceMetadata
} from '@/lib/api/analysis';
import ReactMarkdown from 'react-markdown';

interface PinnedCompanyCardProps {
  companyId: string;
  companyName: string;
  companyTicker: string;
  onUnpin: () => void;
  onClick: () => void;
}

// Helper to get score color
const getScoreColor = (score: number) => {
  if (score >= 80) return "text-emerald-500 bg-emerald-500/10 border-emerald-500/20";
  if (score >= 60) return "text-amber-500 bg-amber-500/10 border-amber-500/20";
  return "text-red-500 bg-red-500/10 border-red-500/20";
};

// Helper to get decision color and icon
const getDecisionStyle = (decision: string) => {
  const upperDecision = decision?.toUpperCase() || '';

  // Positive decisions
  if (['BUY', 'ENGAGE', 'APPROVE', 'APPROVE CREDIT', 'OVERWEIGHT'].includes(upperDecision)) {
    return { color: 'text-emerald-400', bg: 'bg-emerald-500/20', border: 'border-emerald-500/50', Icon: TrendingUp };
  }
  // Negative decisions
  if (['SELL', 'AVOID', 'REJECT', 'REJECT CREDIT', 'UNDERWEIGHT'].includes(upperDecision)) {
    return { color: 'text-red-400', bg: 'bg-red-500/20', border: 'border-red-500/50', Icon: TrendingDown };
  }
  // Neutral decisions
  return { color: 'text-amber-400', bg: 'bg-amber-500/20', border: 'border-amber-500/50', Icon: Scale };
};

// Get persona label
const getPersonaLabel = (persona: string | undefined) => {
  switch (persona) {
    case 'INVESTOR': return 'Investor';
    case 'RELATIONSHIP_MANAGER': return 'Relationship Manager';
    case 'CREDIT_RISK': return 'Credit Risk Analyst';
    case 'MARKET_ANALYST': return 'Market Analyst';
    default: return 'Investor';
  }
};

// Simple citation components for markdown
const createSimpleCitationComponents = () => ({
  p: ({ children, ...props }: any) => <p className="mb-2 last:mb-0" {...props}>{children}</p>,
  ul: ({ children, ...props }: any) => <ul className="list-disc pl-5 my-2 space-y-1 text-gray-300" {...props}>{children}</ul>,
  li: ({ children, ...props }: any) => <li {...props}>{children}</li>,
  strong: ({ children, ...props }: any) => <strong className="font-bold text-white" {...props}>{children}</strong>,
});

// Helper to format time ago
const formatTimeAgo = (dateString: string) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
};

export function PinnedCompanyCard({ companyId, companyName, companyTicker, onUnpin, onClick }: PinnedCompanyCardProps) {
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        setLoading(true);
        const reports = await analysisApi.getReports(companyId);
        if (reports && reports.length > 0) {
          // Get the most recent report
          setReport(reports[0]);
        } else {
          setError('No analysis available');
        }
      } catch (err) {
        console.error('Error fetching analysis report:', err);
        setError('Failed to load analysis');
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [companyId]);

  // Loading state
  if (loading) {
    return (
      <GlassCard className="p-6 min-h-[200px] flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="animate-spin text-indigo-500 mx-auto mb-2" size={24} />
          <p className="text-sm text-gray-400">Loading {companyName}...</p>
        </div>
      </GlassCard>
    );
  }

  // Error/No report state
  if (error || !report) {
    return (
      <GlassCard className="p-6 min-h-[200px] border-l-4 border-l-gray-500/50">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="font-bold text-white">{companyName}</h3>
            <span className="text-xs text-gray-400">{companyTicker}</span>
          </div>
          <button
            onClick={(e) => { e.stopPropagation(); onUnpin(); }}
            className="p-1.5 rounded-lg hover:bg-red-500/10 text-gray-400 hover:text-red-400 transition-colors"
            title="Unpin"
          >
            <X size={16} />
          </button>
        </div>
        <div className="flex items-center justify-center flex-1 py-8">
          <div className="text-center">
            <AlertTriangle className="text-amber-500 mx-auto mb-2" size={24} />
            <p className="text-sm text-gray-400">{error || 'No analysis available'}</p>
            <button
              onClick={onClick}
              className="mt-2 text-xs text-indigo-400 hover:text-indigo-300"
            >
              Run Analysis →
            </button>
          </div>
        </div>
      </GlassCard>
    );
  }

  const insight = getRoleBasedInsight(report);
  const decisionStyle = getDecisionStyle(insight.decision);
  const citationComponents = createSimpleCitationComponents();

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
    >
      <GlassCard
        className={cn("p-5 cursor-pointer hover:border-white/20 transition-all border-l-4", decisionStyle.border)}
        onClick={onClick}
      >
        {/* Header with company name and unpin */}
        <div className="flex justify-between items-start mb-3">
          <div className="flex items-center gap-3">
            <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center", decisionStyle.bg)}>
              <decisionStyle.Icon size={20} className={decisionStyle.color} />
            </div>
            <div>
              <h3 className="font-bold text-white text-sm">{companyName}</h3>
              <span className="text-xs text-gray-400">{companyTicker}</span>
            </div>
          </div>
          <button
            onClick={(e) => { e.stopPropagation(); onUnpin(); }}
            className="p-1.5 rounded-lg hover:bg-red-500/10 text-gray-400 hover:text-red-400 transition-colors"
            title="Unpin"
          >
            <X size={16} />
          </button>
        </div>

        {/* Decision and Confidence */}
        <div className="flex items-center gap-2 mb-3">
          <h2 className={cn("text-lg font-bold", decisionStyle.color)}>
            {insight.decision}
          </h2>
          <div className="ml-auto flex items-center gap-2">
            <div
              className="p-1 rounded text-gray-500 hover:text-gray-300 transition-colors cursor-help"
              title={`Last updated: ${new Date(report.created_at).toLocaleString()}`}
            >
              <Clock size={14} />
            </div>
            <div className={cn("px-2 py-0.5 rounded text-xs font-bold border", getScoreColor(insight.confidence_score))}>
              {insight.confidence_score}%
            </div>
          </div>
        </div>

        {/* Justification (truncated) */}
        <div className="border-t border-white/10 pt-3">
          <div className="text-xs text-gray-300 line-clamp-2">
            <ReactMarkdown components={citationComponents}>
              {insight.justification?.replace(/\[[^\]]+\]/g, '').substring(0, 150) + '...'}
            </ReactMarkdown>
          </div>
        </div>
      </GlassCard>
    </motion.div>
  );
}
