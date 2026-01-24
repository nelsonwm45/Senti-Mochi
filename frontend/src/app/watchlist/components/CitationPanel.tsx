import { SourceReference } from '@/lib/api/analysis';
import { GlassCard } from '@/components/ui/GlassCard';
import { X, ExternalLink } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Mock data store for now, in real app this would likely fetch from an endpoint or Context
const mockSources = new Map<string, SourceReference>();

interface CitationPanelProps {
    citationId: string | null;
    onClose: () => void;
}

export function CitationPanel({ citationId, onClose }: CitationPanelProps) {
    if (!citationId) return null;

    // In a real implementation, we'd lookup the actual source content
    // For this demo, we'll parse the ID (e.g., N1 -> News 1)
    const type = citationId.startsWith('N') ? 'News' : citationId.startsWith('F') ? 'Financial Report' : 'Document';
    
    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="fixed bottom-6 right-6 z-50 w-80 shadow-2xl"
            >
                <GlassCard className="border border-white/20 bg-black/80 backdrop-blur-xl">
                    <div className="flex justify-between items-start mb-3">
                        <div className="flex items-center gap-2">
                            <span className="text-xs font-bold bg-blue-500 text-white px-1.5 rounded">
                                {citationId}
                            </span>
                            <span className="text-sm font-semibold text-gray-300">{type} Source</span>
                        </div>
                        <button onClick={onClose} className="text-gray-400 hover:text-white">
                            <X size={16} />
                        </button>
                    </div>
                    
                    <div className="space-y-2">
                         <div className="h-2 w-20 bg-white/10 rounded animate-pulse" />
                         <div className="h-2 w-full bg-white/10 rounded animate-pulse" />
                         <div className="h-2 w-4/5 bg-white/10 rounded animate-pulse" />
                         <p className="text-xs text-gray-500 mt-2 italic">
                             Fetching source details for {citationId}...
                         </p>
                    </div>

                    <div className="mt-4 pt-3 border-t border-white/10 flex justify-end">
                        <button className="text-xs text-blue-400 flex items-center gap-1 hover:underline">
                            Open complete source <ExternalLink size={10} />
                        </button>
                    </div>
                </GlassCard>
            </motion.div>
        </AnimatePresence>
    );
}
