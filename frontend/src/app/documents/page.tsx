'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
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
      <div className="min-h-full p-4 md:p-8">
        <div className="max-w-7xl mx-auto space-y-8">
          {/* Header */}
          <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-start gap-4"
          >
            <div className="p-3 bg-gradient-brand rounded-xl shadow-lg shadow-accent/20">
              <FileText className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-brand bg-clip-text text-transparent leading-tight">
                Documents
              </h1>
              <p className="text-base text-foreground-muted">
                Upload and manage your financial documents for AI-powered analysis
              </p>
            </div>
          </motion.div>

          {/* Upload Zone */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <UploadZone onUploadSuccess={handleUploadSuccess} />
          </motion.div>

          {/* Document List */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-foreground">
                Your Documents
              </h2>
            </div>
            <DocumentList />
          </motion.div>
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
          <Loader2 className="w-8 h-8 text-accent animate-spin" />
        </div>
      }>
        <DocumentsContent />
      </Suspense>
    </ProtectedLayout>
  );
}
