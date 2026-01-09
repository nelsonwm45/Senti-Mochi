'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { X, FileText, Copy, Loader2, AlertCircle, Download, Calendar, HardDrive } from 'lucide-react';
import { Document } from '@/lib/api/documents';
import { useDocumentContent } from '@/hooks/useDocuments';
import { toast } from 'react-hot-toast';

interface DocumentViewerModalProps {
  isOpen: boolean;
  onClose: () => void;
  document: Document | null;
}

export default function DocumentViewerModal({
  isOpen,
  onClose,
  document,
}: DocumentViewerModalProps) {
  const { data, isLoading, error } = useDocumentContent(document?.id || '');

  if (!document) return null;

  const handleCopy = () => {
    if (data?.chunks) {
      const fullText = data.chunks.map((c: { content: string }) => c.content).join('\n\n');
      navigator.clipboard.writeText(fullText);
      toast.success('Content copied to clipboard');
    }
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleBackdropClick}
            className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 sm:p-6"
          >
            {/* Modal Window */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ type: 'spring', duration: 0.5, bounce: 0.2 }}
              className="bg-white dark:bg-gray-900 w-full max-w-5xl h-[85vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-gray-200 dark:border-gray-800"
              onClick={(e) => e.stopPropagation()}
            >
              
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900 z-10">
                <div className="flex items-center space-x-4 overflow-hidden">
                  <div className="p-2.5 bg-blue-50 dark:bg-blue-900/20 rounded-xl flex-shrink-0">
                    <FileText className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div className="min-w-0">
                    <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100 truncate">
                      {document.filename}
                    </h2>
                    <div className="flex items-center space-x-3 text-xs text-gray-500 dark:text-gray-400 mt-1">
                      <span className="flex items-center">
                        <HardDrive className="w-3.5 h-3.5 mr-1" />
                        {(document.fileSize / 1024).toFixed(1)} KB
                      </span>
                      <span className="w-1 h-1 bg-gray-300 dark:bg-gray-700 rounded-full" />
                      <span className="flex items-center">
                        <Calendar className="w-3.5 h-3.5 mr-1" />
                        {new Date(document.uploadDate).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2 pl-4">
                  <button
                    onClick={handleCopy}
                    className="p-2 text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-xl transition-all duration-200 group"
                    title="Copy Content"
                  >
                    <Copy className="w-5 h-5 transition-transform group-hover:scale-110" />
                  </button>
                  <button
                    onClick={onClose}
                    className="p-2 text-gray-400 hover:text-red-500 dark:text-gray-500 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/20 rounded-xl transition-all duration-200"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Toolbar / Actions Bar (Optional future use, kept clean for now) */}
              
              {/* Content Area */}
              <div className="flex-1 overflow-hidden relative bg-gray-50/50 dark:bg-gray-950">
                <div className="absolute inset-0 overflow-y-auto custom-scrollbar p-6 sm:p-10">
                  <div className="max-w-4xl mx-auto">
                    {isLoading ? (
                      <div className="flex flex-col items-center justify-center h-64 space-y-4">
                        <Loader2 className="w-10 h-10 text-blue-500 animate-spin" />
                        <p className="text-sm font-medium text-gray-500 dark:text-gray-400 animate-pulse">
                          Loading document content...
                        </p>
                      </div>
                    ) : error ? (
                      <div className="flex flex-col items-center justify-center h-64 text-center p-8 bg-red-50 dark:bg-red-950/10 rounded-2xl border border-red-100 dark:border-red-900/50">
                        <div className="p-3 bg-red-100 dark:bg-red-900/20 rounded-full mb-3">
                          <AlertCircle className="w-8 h-8 text-red-500 dark:text-red-400" />
                        </div>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                          Unable to load content
                        </h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400 max-w-xs mx-auto">
                          There was an error retrieving the document text. Please try again later.
                        </p>
                      </div>
                    ) : (
                      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-100 dark:border-gray-800 min-h-[500px] p-8 relative">
                        {/* Paper Effect Highlight */}
                        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500/0 via-blue-500/10 to-blue-500/0" />
                        
                        <div className="max-w-none">
                          {data?.chunks ? (
                            <div className="space-y-3">
                              {data.chunks.map((chunk: { content: string; start_line: number; end_line: number; page_number?: number }, index: number) => (
                                <div key={index} className="relative rounded-2xl border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 overflow-hidden shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-[1.01]">
                                  {/* Premium Header Bar */}
                                  <div className="bg-gradient-to-r from-blue-600 via-blue-500 to-purple-600 h-2"></div>
                                  
                                  {/* Content */}
                                  <div className="p-8">
                                    <p className="text-sm leading-relaxed text-gray-900 dark:text-gray-100 whitespace-pre-wrap font-sans">
                                      {chunk.content}
                                    </p>
                                  </div>
                                  
                                  {/* Bottom accent */}
                                  <div className="h-1 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 dark:from-gray-700 dark:via-gray-600 dark:to-gray-700"></div>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <div className="text-center py-20 text-gray-400 italic">
                              No content available for this document.
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

               {/* Footer */}
               <div className="px-6 py-3 bg-white dark:bg-gray-900 border-t border-gray-100 dark:border-gray-800 flex items-center justify-between text-xs text-gray-400 dark:text-gray-500">
                <div>
                   Parsed content view
                </div>
                <div className="flex items-center space-x-2">
                   <span className="w-2 h-2 rounded-full bg-green-500"></span>
                   <span>Ready to chat</span>
                </div>
              </div>

            </motion.div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
