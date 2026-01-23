'use client';

import { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, FileText, ExternalLink } from 'lucide-react';
import { CitationInfo } from '@/lib/api/chat';
import { GlassCard } from '@/components/ui/GlassCard';
import apiClient from '@/lib/apiClient';

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

  const handleLinkClick = async (e: React.MouseEvent, url: string) => {
    e.stopPropagation();
    e.preventDefault();
    
    try {
      // If it's a backend document link, we need to fetch the file content (proxy)
      if (url.includes('/api/v1/documents')) {
         // Extract relative path if it's a full URL
         const relativeUrl = url.replace(/^https?:\/\/[^\/]+/, '');
         
         const response = await apiClient.get(relativeUrl, { 
            responseType: 'blob' 
         });
         
         // Create blob URL
         const blob = new Blob([response.data], { type: response.headers['content-type'] || 'application/pdf' });
         const blobUrl = window.URL.createObjectURL(blob);
         window.open(blobUrl, '_blank');
         
         // Note: We're not revoking the URL immediately so the new tab can load it.
         // Ideally we track it and revoke later.
      } else {
         // External link (news)
         window.open(url, '_blank');
      }
    } catch (err) {
      console.error("Failed to open link:", err);
      // Fallback
      window.open(url, '_blank');
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
            onClick={onClose}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
          />

          {/* Panel */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed top-0 right-0 h-full w-full max-w-md bg-glass-bg border-l border-glass-border shadow-2xl z-50 flex flex-col backdrop-blur-xl"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-glass-border">
              <h2 className="text-xl font-semibold text-foreground">
                Sources ({citations.length})
              </h2>
              <button
                onClick={onClose}
                className="p-2 hover:bg-white/10 rounded-lg transition-colors text-foreground-muted hover:text-foreground"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Citations List */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {citations.length === 0 ? (
                <div className="text-center py-12">
                  <FileText className="w-12 h-12 text-foreground-muted opacity-50 mx-auto mb-3" />
                  <p className="text-foreground-muted">
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
                  >
                    <GlassCard 
                      variant={isActive ? 'interactive' : 'default'}
                      className={`p-4 cursor-pointer transition-all ${
                        isActive 
                          ? 'ring-2 ring-accent border-accent/50 bg-accent/5' 
                          : 'hover:border-accent/30'
                      }`}
                      onClick={() => onCitationClick?.(citation)}
                    >
                      {/* Citation Number */}
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center space-x-3">
                          <div className={`w-8 h-8 rounded-lg flex items-center justify-center shadow-lg transition-all ${
                            isActive
                              ? 'bg-accent text-white scale-110'
                              : 'bg-gradient-to-br from-blue-500/20 to-purple-600/20 text-accent'
                          }`}>
                            <span className="text-sm font-bold">
                              {citation.sourceNumber}
                            </span>
                          </div>
                          <div className={`font-medium transition-colors ${isActive ? 'text-accent' : 'text-foreground'}`}>
                            Source {citation.sourceNumber}
                          </div>
                        </div>
                        {citation.url ? (
                          <button 
                            onClick={(e) => handleLinkClick(e, citation.url!)}
                            className="p-1 hover:bg-accent/10 rounded-full transition-colors"
                            title="Open Source"
                          >
                            <ExternalLink className={`w-4 h-4 transition-colors ${isActive ? 'text-accent' : 'text-foreground-muted hover:text-accent'}`} />
                          </button>
                        ) : (
                          <ExternalLink className={`w-4 h-4 transition-colors ${isActive ? 'text-accent' : 'text-foreground-muted'}`} />
                        )}
                      </div>

                      {/* Document Info */}
                      <div className="space-y-3 pl-1">
                        <div className="flex items-center space-x-2 text-sm">
                          <FileText className="w-4 h-4 text-accent flex-shrink-0" />
                          <span className="text-foreground-secondary font-medium truncate">
                            {citation.filename}
                          </span>
                        </div>

                        <div className="flex items-center gap-2 flex-wrap">
                          {citation.pageNumber && (
                            <div className="text-xs font-mono text-foreground-muted bg-accent/5 border border-accent/10 px-2 py-1 rounded">
                              Page {citation.pageNumber}
                            </div>
                          )}
                          {citation.startLine && citation.endLine && (
                            <div className="text-xs font-mono text-foreground-muted bg-accent/5 border border-accent/10 px-2 py-1 rounded">
                              Lines {citation.startLine}-{citation.endLine}
                            </div>
                          )}
                        </div>

                        {/* Text Snippet */}
                        {citation.text && (
                          <div className="mt-2 text-sm text-foreground-secondary bg-black/5 dark:bg-black/20 p-3 rounded-lg border border-black/5 dark:border-white/5 italic">
                             <p className="line-clamp-4">
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
                          <span className="text-[10px] font-medium text-foreground-muted">
                            Match: {(citation.similarity * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    </GlassCard>
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
