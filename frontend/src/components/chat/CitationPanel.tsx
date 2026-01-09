'use client';

import { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, FileText, ExternalLink } from 'lucide-react';
import { CitationInfo } from '@/lib/api/chat';

interface CitationPanelProps {
  citations: CitationInfo[];
  isOpen: boolean;
  onClose: () => void;
  onCitationClick?: (citation: CitationInfo) => void;
  activeCitationId?: number | null;
}

export default function CitationPanel({
  citations,
  isOpen,
  onClose,
  onCitationClick,
  activeCitationId,
}: CitationPanelProps) {
  // Scroll to active citation when it changes
  useEffect(() => {
    if (activeCitationId && isOpen) {
        const element = document.getElementById(`citation-${activeCitationId}`);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
  }, [activeCitationId, isOpen]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          />

          {/* Panel */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed top-0 right-0 h-full w-full max-w-md bg-white dark:bg-gray-800 shadow-2xl z-50 flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                Sources ({citations.length})
              </h2>
              <button
                onClick={onClose}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              </button>
            </div>

            {/* Citations List */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {citations.length === 0 ? (
                <div className="text-center py-12">
                  <FileText className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-600 dark:text-gray-400">
                    No sources found
                  </p>
                </div>
              ) : (
                citations.map((citation, index) => {
                  const isActive = activeCitationId === citation.sourceNumber;
                  return (
                  <motion.div
                    key={citation.chunkId}
                    id={`citation-${citation.sourceNumber}`}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className={`rounded-xl p-4 border transition-all cursor-pointer ${
                      isActive 
                        ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-500 shadow-sm ring-1 ring-blue-500' 
                        : 'bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700'
                    }`}
                    onClick={() => onCitationClick?.(citation)}
                  >
                    {/* Citation Number */}
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center space-x-2">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                          isActive
                            ? 'bg-blue-600 shadow-lg shadow-blue-500/30'
                            : 'bg-gradient-to-br from-blue-500 to-purple-600'
                        }`}>
                          <span className="text-sm font-bold text-white">
                            {citation.sourceNumber}
                          </span>
                        </div>
                        <div className={`font-medium ${isActive ? 'text-blue-700 dark:text-blue-300' : 'text-gray-900 dark:text-white'}`}>
                          Source {citation.sourceNumber}
                        </div>
                      </div>
                      <ExternalLink className={`w-4 h-4 ${isActive ? 'text-blue-500' : 'text-gray-400'}`} />
                    </div>

                    {/* Document Info */}
                    <div className="space-y-3">
                      <div className="flex items-center space-x-2 text-sm">
                        <FileText className="w-4 h-4 text-blue-500 flex-shrink-0" />
                        <span className="text-gray-700 dark:text-gray-300 font-medium truncate">
                          {citation.filename}
                        </span>
                      </div>

                      <div className="flex items-center space-x-2">
                        {citation.pageNumber && (
                          <div className="text-xs font-mono text-gray-500 dark:text-gray-400 bg-gray-200 dark:bg-gray-800 px-2 py-1 rounded w-fit">
                            Page {citation.pageNumber}
                          </div>
                        )}
                        {citation.startLine && citation.endLine && (
                          <div className="text-xs font-mono text-gray-500 dark:text-gray-400 bg-gray-200 dark:bg-gray-800 px-2 py-1 rounded w-fit">
                            Lines {citation.startLine}-{citation.endLine}
                          </div>
                        )}
                      </div>

                      {/* Text Snippet */}
                      {citation.text && (
                        <div className="mt-2 text-sm text-gray-600 dark:text-gray-300 bg-white dark:bg-black/20 p-3 rounded-lg border border-gray-100 dark:border-gray-800">
                           <p className="line-clamp-4 italic">
                             "{citation.text}"
                           </p>
                        </div>
                      )}

                      {/* Similarity Score */}
                      <div className="flex items-center space-x-2 pt-1">
                        <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-blue-500 to-purple-600 rounded-full transition-all"
                            style={{ width: `${citation.similarity * 100}%` }}
                          />
                        </div>
                        <span className="text-[10px] font-medium text-gray-500 dark:text-gray-400">
                          Match: {(citation.similarity * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </motion.div>
                )})
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
