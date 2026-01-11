'use client';

import { useState } from 'react';
import { useDocuments } from '@/hooks/useDocuments';
import DocumentCard from './DocumentCard';
import { FileX, Loader2 } from 'lucide-react';
import { GlassCard } from '@/components/ui/GlassCard';
import { motion } from 'framer-motion';

export default function DocumentList() {
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const { data, isLoading, error } = useDocuments({ status: statusFilter });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="p-4 bg-glass-bg border border-glass-border rounded-full shadow-lg backdrop-blur-md">
          <Loader2 className="w-8 h-8 text-accent animate-spin" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <GlassCard className="inline-block p-6 border-red-500/30 bg-red-500/5">
          <p className="text-red-500 font-medium">
            Failed to load documents. Please try again.
          </p>
        </GlassCard>
      </div>
    );
  }

  const documents = data?.documents || [];

  return (
    <div className="space-y-6">
      {/* Filter Tabs */}
      {/* Filter Tabs (Segmented Control) */}
      <div className="bg-glass-border/30 dark:bg-glass-border/10 p-1.5 rounded-xl inline-flex relative w-full sm:w-auto overflow-hidden">
        {['all', 'PROCESSED', 'PROCESSING', 'PENDING', 'FAILED'].map((status) => {
          const isActive = statusFilter === status || (status === 'all' && !statusFilter);
          return (
            <button
              key={status}
              onClick={() => setStatusFilter(status === 'all' ? undefined : status)}
              className={`
                relative px-4 py-2 text-sm font-medium rounded-lg transition-all duration-300 z-10 flex-1 sm:flex-none text-center
                ${isActive
                  ? 'text-foreground font-semibold'
                  : 'text-foreground-muted hover:text-foreground'
                }
              `}
            >
              {isActive && (
                <motion.div
                  className="absolute inset-0 bg-white dark:bg-slate-700 shadow-sm z-[-1] rounded-lg"
                  layoutId="activeTab"
                  transition={{ type: "spring", stiffness: 300, damping: 30 }}
                />
              )}
              {status === 'all' ? 'All' : status.charAt(0) + status.slice(1).toLowerCase()}
            </button>
          );
        })}
      </div>

      {/* Document Grid */}
      {documents.length === 0 ? (
        <GlassCard className="flex flex-col items-center justify-center py-16 text-center border-dashed">
          <div className="p-6 bg-glass-bg rounded-full mb-4 shadow-inner">
            <FileX className="w-12 h-12 text-foreground-muted opacity-50" />
          </div>
          <h3 className="text-lg font-bold text-foreground mb-2">
            No documents yet
          </h3>
          <p className="text-foreground-muted max-w-md">
            Upload your first document to get started with AI-powered analysis
          </p>
        </GlassCard>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {documents.map((document) => (
            <DocumentCard key={document.id} document={document} />
          ))}
        </div>
      )}

      {/* Document Count */}
      {documents.length > 0 && (
        <div className="text-center text-sm text-foreground-muted">
          Showing {documents.length} document{documents.length !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  );
}
