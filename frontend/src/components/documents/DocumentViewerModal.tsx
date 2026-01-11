'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { X, FileText, Copy, Loader2, AlertCircle, HardDrive, Calendar } from 'lucide-react';
import { Document } from '@/lib/api/documents';
import { useDocumentContent } from '@/hooks/useDocuments';
import { toast } from 'react-hot-toast';
import { GlassCard } from '@/components/ui/GlassCard';
import { GlassButton } from '@/components/ui/GlassButton';

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
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 sm:p-6"
          >
            {/* Modal Window */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ type: 'spring', duration: 0.5, bounce: 0.2 }}
              className="w-full max-w-5xl h-[85vh] flex flex-col relative z-50"
              onClick={(e) => e.stopPropagation()}
            >
              <GlassCard className="h-full flex flex-col p-0 overflow-hidden border-2 border-glass-border">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-glass-border bg-glass-bg/50 backdrop-blur-md z-10">
                  <div className="flex items-center space-x-4 overflow-hidden">
                    <div className="p-2.5 bg-gradient-brand rounded-xl flex-shrink-0 shadow-lg shadow-accent/20">
                      <FileText className="w-6 h-6 text-white" />
                    </div>
                    <div className="min-w-0">
                      <h2 className="text-lg font-bold text-foreground truncate">
                        {document.filename}
                      </h2>
                      <div className="flex items-center space-x-3 text-xs text-foreground-muted mt-1">
                        <span className="flex items-center">
                          <HardDrive className="w-3.5 h-3.5 mr-1 text-accent" />
                          {(document.fileSize / 1024).toFixed(1)} KB
                        </span>
                        <span className="w-1 h-1 bg-glass-border rounded-full" />
                        <span className="flex items-center">
                          <Calendar className="w-3.5 h-3.5 mr-1 text-accent" />
                          {new Date(document.uploadDate).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 pl-4">
                    <GlassButton
                      onClick={handleCopy}
                      size="sm"
                      variant="ghost"
                      className="!px-2"
                      title="Copy Content"
                    >
                      <Copy className="w-5 h-5" />
                    </GlassButton>
                    <GlassButton
                      onClick={onClose}
                      size="sm"
                      variant="ghost" 
                      className="!px-2 hover:bg-red-500/10 hover:text-red-500"
                    >
                      <X className="w-5 h-5" />
                    </GlassButton>
                  </div>
                </div>

                {/* Content Area */}
                <div className="flex-1 overflow-hidden relative bg-glass-bg/30">
                  <div className="absolute inset-0 overflow-y-auto custom-scrollbar p-6 sm:p-10">
                    <div className="max-w-4xl mx-auto">
                      {isLoading ? (
                        <div className="flex flex-col items-center justify-center h-64 space-y-4">
                          <Loader2 className="w-10 h-10 text-accent animate-spin" />
                          <p className="text-sm font-medium text-foreground-muted animate-pulse">
                            Loading document content...
                          </p>
                        </div>
                      ) : error ? (
                        <div className="flex flex-col items-center justify-center h-64 text-center p-8 bg-red-500/5 rounded-2xl border border-red-500/20">
                          <div className="p-3 bg-red-500/10 rounded-full mb-3">
                            <AlertCircle className="w-8 h-8 text-red-500" />
                          </div>
                          <h3 className="text-lg font-semibold text-foreground mb-1">
                            Unable to load content
                          </h3>
                          <p className="text-sm text-foreground-muted max-w-xs mx-auto">
                            There was an error retrieving the document text. Please try again later.
                          </p>
                        </div>
                      ) : (
                        <div className="min-h-[500px]">
                          {data?.chunks ? (
                            <div className="space-y-4">
                              {data.chunks.map((chunk: { content: string; start_line: number; end_line: number; page_number?: number }, index: number) => (
                                <GlassCard 
                                  key={index}
                                  className="relative !p-0 overflow-hidden hover:border-accent/30 transition-all duration-300"
                                >
                                  {/* Premium Header Bar */}
                                  <div className="bg-gradient-brand h-1.5 opacity-80"></div>
                                  
                                  {/* Content */}
                                  <div className="p-8">
                                    <p className="text-sm leading-relaxed text-foreground whitespace-pre-wrap font-sans">
                                      {chunk.content}
                                    </p>
                                  </div>
                                </GlassCard>
                              ))}
                            </div>
                          ) : (
                            <div className="text-center py-20 text-foreground-muted italic">
                              No content available for this document.
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                 {/* Footer */}
                 <div className="px-6 py-3 border-t border-glass-border bg-glass-bg/50 backdrop-blur-md flex items-center justify-between text-xs text-foreground-muted">
                  <div>
                     Parsed content view
                  </div>
                  <div className="flex items-center space-x-2">
                     <span className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]"></span>
                     <span>Ready to chat</span>
                  </div>
                </div>
              </GlassCard>
            </motion.div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
