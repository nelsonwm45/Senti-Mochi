'use client';

import { Document } from '@/lib/api/documents';
import { FileText, Trash2, RefreshCw, Clock, CheckCircle, AlertCircle, Loader2, Eye } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { useDeleteDocument, useReprocessDocument } from '@/hooks/useDocuments';
import { useRouter, useSearchParams } from 'next/navigation';
import { GlassCard } from '@/components/ui/GlassCard';

interface DocumentCardProps {
  document: Document;
}

interface StatusConfigItem {
  icon: any;
  className: string;
  label: string;
  spin?: boolean;
}

const STATUS_CONFIG: Record<string, StatusConfigItem> = {
  PENDING: {
    icon: Clock,
    className: 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20',
    label: 'Pending',
  },
  PROCESSING: {
    icon: Loader2,
    className: 'text-blue-500 bg-blue-500/10 border-blue-500/20',
    label: 'Processing',
    spin: true,
  },
  PROCESSED: {
    icon: CheckCircle,
    className: 'text-green-500 bg-green-500/10 border-green-500/20',
    label: 'Processed',
  },
  FAILED: {
    icon: AlertCircle,
    className: 'text-red-500 bg-red-500/10 border-red-500/20',
    label: 'Failed',
  },
};

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DocumentCard({ document }: DocumentCardProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const deleteMutation = useDeleteDocument();
  const reprocessMutation = useReprocessDocument();

  const statusConfig = STATUS_CONFIG[document.status];
  const StatusIcon = statusConfig.icon;

  const handleDelete = () => {
    if (confirm(`Delete "${document.filename}"?`)) {
      deleteMutation.mutate(document.id);
    }
  };

  const handleReprocess = () => {
    reprocessMutation.mutate(document.id);
  };

  const handleView = () => {
    const params = new URLSearchParams(searchParams.toString());
    params.set('view', document.id);
    router.push(`/documents?${params.toString()}`);
  };

  return (
    <GlassCard className="p-6 h-full flex flex-col hover:shadow-lg hover:border-accent/30 transition-all duration-300 group">
      {/* Header with Icon and Status */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3 w-full">
          <div className="p-3 bg-gradient-brand rounded-xl shadow-lg shadow-accent/10 flex-shrink-0">
            <FileText className="w-6 h-6 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-bold text-foreground truncate group-hover:text-accent transition-colors">
              {document.filename}
            </h3>
            <p className="text-xs text-foreground-muted mt-1 font-mono">
              {formatFileSize(document.fileSize)} • {formatDistanceToNow(new Date(document.uploadDate), { addSuffix: true })}
            </p>
          </div>
        </div>
      </div>

      <div className="flex-grow">
        {/* Status Badge */}
        <div className={`
          inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg border backdrop-blur-sm mb-4
          ${statusConfig.className}
        `}>
          <StatusIcon className={`w-4 h-4 ${statusConfig.spin ? 'animate-spin' : ''}`} />
          <span className="text-sm font-medium">
            {statusConfig.label}
          </span>
        </div>

        {/* Error Message */}
        {document.errorMessage && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
            <p className="text-xs text-red-500">
              {document.errorMessage}
            </p>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center justify-end space-x-2 pt-4 border-t border-glass-border mt-auto">
        <button
          onClick={handleView}
          className="p-2 text-foreground-muted hover:text-accent hover:bg-glass-bg rounded-lg transition-colors"
          title="View Content"
        >
          <Eye className="w-5 h-5" />
        </button>

        {document.status === 'FAILED' && (
          <button
            onClick={handleReprocess}
            disabled={reprocessMutation.isPending}
            className="p-2 text-blue-500 hover:bg-blue-500/10 rounded-lg transition-colors disabled:opacity-50"
            title="Reprocess"
          >
            <RefreshCw className={`w-5 h-5 ${reprocessMutation.isPending ? 'animate-spin' : ''}`} />
          </button>
        )}
        
        <button
          onClick={handleDelete}
          disabled={deleteMutation.isPending}
          className="p-2 text-foreground-muted hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-colors disabled:opacity-50"
          title="Delete"
        >
          <Trash2 className="w-5 h-5" />
        </button>
      </div>
    </GlassCard>
  );
}
