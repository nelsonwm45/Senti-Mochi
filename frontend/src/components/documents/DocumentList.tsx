'use client';

import { useState } from 'react';
import { useDocuments } from '@/hooks/useDocuments';
import DocumentCard from './DocumentCard';
import { FileX, Loader2 } from 'lucide-react';

export default function DocumentList() {
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const { data, isLoading, error } = useDocuments({ status: statusFilter });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 dark:text-red-400">
          Failed to load documents. Please try again.
        </p>
      </div>
    );
  }

  const documents = data?.documents || [];

  return (
    <div className="space-y-6">
      {/* Filter Tabs */}
      <div className="flex items-center space-x-2 border-b border-gray-200 dark:border-gray-700">
        {['all', 'PROCESSED', 'PROCESSING', 'PENDING', 'FAILED'].map((status) => (
          <button
            key={status}
            onClick={() => setStatusFilter(status === 'all' ? undefined : status)}
            className={`
              px-4 py-2 text-sm font-medium border-b-2 transition-colors
              ${(statusFilter === status || (status === 'all' && !statusFilter))
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
              }
            `}
          >
            {status === 'all' ? 'All' : status.charAt(0) + status.slice(1).toLowerCase()}
          </button>
        ))}
      </div>

      {/* Document Grid */}
      {documents.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16">
          <div className="p-6 bg-gray-100 dark:bg-gray-800 rounded-full mb-4">
            <FileX className="w-12 h-12 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            No documents yet
          </h3>
          <p className="text-gray-600 dark:text-gray-400 text-center max-w-md">
            Upload your first document to get started with AI-powered analysis
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {documents.map((document) => (
            <DocumentCard key={document.id} document={document} />
          ))}
        </div>
      )}

      {/* Document Count */}
      {documents.length > 0 && (
        <div className="text-center text-sm text-gray-500 dark:text-gray-400">
          Showing {documents.length} document{documents.length !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  );
}
