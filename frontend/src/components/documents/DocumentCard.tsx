'use client';

import { Document } from '@/lib/api/documents';
import { FileText, Download, Trash2, RefreshCw, Clock, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { useDeleteDocument, useReprocessDocument } from '@/hooks/useDocuments';

interface DocumentCardProps {
  document: Document;
}

const STATUS_CONFIG = {
  PENDING: {
    icon: Clock,
    color: 'text-yellow-500',
    bg: 'bg-yellow-50 dark:bg-yellow-950/20',
    border: 'border-yellow-200 dark:border-yellow-800',
    label: 'Pending',
  },
  PROCESSING: {
    icon: Loader2,
    color: 'text-blue-500',
    bg: 'bg-blue-50 dark:bg-blue-950/20',
    border: 'border-blue-200 dark:border-blue-800',
    label: 'Processing',
    spin: true,
  },
  PROCESSED: {
    icon: CheckCircle,
    color: 'text-green-500',
    bg: 'bg-green-50 dark:bg-green-950/20',
    border: 'border-green-200 dark:border-green-800',
    label: 'Processed',
  },
  FAILED: {
    icon: AlertCircle,
    color: 'text-red-500',
    bg: 'bg-red-50 dark:bg-red-950/20',
    border: 'border-red-200 dark:border-red-800',
    label: 'Failed',
  },
};

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DocumentCard({ document }: DocumentCardProps) {
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

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md transition-shadow duration-200">
      {/* Header with Icon and Status */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg">
            <FileText className="w-6 h-6 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
              {document.filename}
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {formatFileSize(document.fileSize)} • {formatDistanceToNow(new Date(document.uploadDate), { addSuffix: true })}
            </p>
          </div>
        </div>
      </div>

      {/* Status Badge */}
      <div className={`flex items-center space-x-2 px-3 py-2 rounded-lg ${statusConfig.bg} ${statusConfig.border} border mb-4`}>
        <StatusIcon className={`w-4 h-4 ${statusConfig.color} ${statusConfig.spin ? 'animate-spin' : ''}`} />
        <span className={`text-sm font-medium ${statusConfig.color}`}>
          {statusConfig.label}
        </span>
      </div>

      {/* Error Message */}
      {document.errorMessage && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-600 dark:text-red-400">
            {document.errorMessage}
          </p>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-end space-x-2 pt-4 border-t border-gray-200 dark:border-gray-700">
        {document.status === 'FAILED' && (
          <button
            onClick={handleReprocess}
            disabled={reprocessMutation.isPending}
            className="p-2 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-950/20 rounded-lg transition-colors disabled:opacity-50"
            title="Reprocess"
          >
            <RefreshCw className={`w-5 h-5 ${reprocessMutation.isPending ? 'animate-spin' : ''}`} />
          </button>
        )}
        
        <button
          onClick={handleDelete}
          disabled={deleteMutation.isPending}
          className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/20 rounded-lg transition-colors disabled:opacity-50"
          title="Delete"
        >
          <Trash2 className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
