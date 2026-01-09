'use client';

import UploadZone from '@/components/documents/UploadZone';
import DocumentList from '@/components/documents/DocumentList';
import { FileText } from 'lucide-react';

import ProtectedLayout from '@/components/layouts/ProtectedLayout';

export default function DocumentsPage() {
  return (
    <ProtectedLayout>
      <div className="min-h-full bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center space-x-3 mb-2">
              <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl">
                <FileText className="w-8 h-8 text-white" />
              </div>
              <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
                Documents
              </h1>
            </div>
            <p className="text-lg text-gray-600 dark:text-gray-400">
              Upload and manage your financial documents for AI-powered analysis
            </p>
          </div>

          {/* Upload Zone */}
          <div className="mb-12">
            <UploadZone />
          </div>

          {/* Document List */}
          <div>
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6">
              Your Documents
            </h2>
            <DocumentList />
          </div>
        </div>
      </div>
    </ProtectedLayout>
  );
}
