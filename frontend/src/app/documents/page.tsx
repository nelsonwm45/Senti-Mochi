'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import UploadZone from '@/components/documents/UploadZone';
import DocumentList from '@/components/documents/DocumentList';
import ProcessingCompleteModal from '@/components/documents/ProcessingCompleteModal';
import DocumentViewerModal from '@/components/documents/DocumentViewerModal';
import { FileText, Loader2 } from 'lucide-react';
import { useDocuments, useDocument } from '@/hooks/useDocuments';
import { Document } from '@/lib/api/documents';
import ProtectedLayout from '@/components/layouts/ProtectedLayout';

function DocumentsContent() {
  const [trackedDocId, setTrackedDocId] = useState<string | null>(null);
  const [completedDoc, setCompletedDoc] = useState<Document | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // URL State for view handling
  const searchParams = useSearchParams();
  const router = useRouter();
  const viewId = searchParams.get('view');
  const { data: viewDoc } = useDocument(viewId || '');

  // Poll for document updates
  const { data: documentsData } = useDocuments({ limit: 100 });

  useEffect(() => {
    if (trackedDocId && documentsData?.documents) {
      const doc = documentsData.documents.find((d: Document) => d.id === trackedDocId);
      
      if (doc && doc.status === 'PROCESSED') {
        setCompletedDoc(doc);
        setIsModalOpen(true);
        setTrackedDocId(null); // Stop tracking this one
      } else if (doc && doc.status === 'FAILED') {
        setTrackedDocId(null); // Stop tracking if failed
      }
    }
  }, [documentsData, trackedDocId]);

  const handleUploadSuccess = (docId: string) => {
    setTrackedDocId(docId);
  };

  const handleCloseViewer = () => {
    const params = new URLSearchParams(searchParams.toString());
    params.delete('view');
    router.push(`/documents?${params.toString()}`);
  };

  return (
    <>
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
            <UploadZone onUploadSuccess={handleUploadSuccess} />
          </div>

          {/* Document List */}
          <div>
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6">
              Your Documents
            </h2>
            <DocumentList />
          </div>
        </div>

        <ProcessingCompleteModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          document={completedDoc}
        />

        <DocumentViewerModal
          isOpen={!!viewId}
          onClose={handleCloseViewer}
          document={viewDoc || null}
        />
      </div>
    </>
  );
}

export default function DocumentsPage() {
  return (
    <ProtectedLayout>
      <Suspense fallback={
        <div className="flex items-center justify-center min-h-screen">
          <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
        </div>
      }>
        <DocumentsContent />
      </Suspense>
    </ProtectedLayout>
  );
}
