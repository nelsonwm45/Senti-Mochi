import { useState } from 'react';
import { motion } from 'framer-motion';
import { GlassCard } from '@/components/ui/GlassCard';
import { RefreshCw, TrendingUp, AlertTriangle, MinusCircle, FileText } from 'lucide-react';
import { Verdict } from '@/lib/api/analysis';
import { cn } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';

interface VerdictFlipCardProps {
    verdict: Verdict;
    confidence: number;
}

export function VerdictFlipCard({ verdict, confidence }: VerdictFlipCardProps) {
    const [isFlipped, setIsFlipped] = useState(false);

    const getActionColor = (action: string) => {
        switch (action) {
            case 'BUY': return 'text-emerald-500 border-emerald-500 bg-emerald-500/10';
            case 'SELL': return 'text-red-500 border-red-500 bg-red-500/10';
            case 'HOLD': return 'text-amber-500 border-amber-500 bg-amber-500/10';
            default: return 'text-gray-500 border-gray-500 bg-gray-500/10';
        }
    };

    const getActionIcon = (action: string) => {
        switch (action) {
            case 'BUY': return <TrendingUp size={32} />;
            case 'SELL': return <AlertTriangle size={32} />;
            default: return <MinusCircle size={32} />;
        }
    };

    const getGradient = (action: string) => {
        switch (action) {
            case 'BUY': return 'from-emerald-900/30 to-slate-900/80 border-t-emerald-500';
            case 'SELL': return 'from-red-900/30 to-slate-900/80 border-t-red-500';
            case 'HOLD': return 'from-amber-900/30 to-slate-900/80 border-t-amber-500';
            default: return 'from-gray-900/30 to-slate-900/80 border-t-gray-500';
        }
    };

    return (
        <div className="relative w-full h-[450px]" style={{ perspective: '1000px' }}>
            <motion.div
                className="w-full h-full relative"
                style={{ transformStyle: 'preserve-3d' }}
                animate={{ rotateY: isFlipped ? 180 : 0 }}
                transition={{ duration: 0.6, ease: 'easeInOut' }}
            >
                {/* FRONT FACE WRAPPER */}
                <div
                    className="absolute inset-0 w-full h-full"
                    style={{ 
                        backfaceVisibility: 'hidden', 
                        WebkitBackfaceVisibility: 'hidden',
                        zIndex: isFlipped ? 0 : 10,
                    }}
                >
                    <GlassCard
                        className={cn(
                            "w-full h-full flex flex-col items-center justify-center text-center p-8 border-x border-b border-t-4 border-white/10 hover:border-white/20 cursor-pointer group backdrop-blur-xl bg-gradient-to-b",
                            getGradient(verdict.action)
                        )}
                        onClick={() => setIsFlipped(true)}
                    >
                        <div className="absolute top-4 right-4 text-xs text-gray-400 flex items-center gap-1 opacity-100 transition-opacity">
                            <RefreshCw size={12} /> Flip for Deep Dive
                        </div>

                        <div className={cn(
                            "w-20 h-20 rounded-full flex items-center justify-center border-4 mb-6 shadow-[0_0_30px_rgba(0,0,0,0.3)] bg-opacity-20",
                            getActionColor(verdict.action)
                        )}>
                            {getActionIcon(verdict.action)}
                        </div>

                        <h2 className={cn(
                            "text-4xl font-black tracking-tighter mb-2",
                            getActionColor(verdict.action).split(' ')[0]
                        )}>
                            {verdict.action}
                        </h2>

                        <div className="text-sm font-semibold text-gray-400 mb-6 uppercase tracking-widest">
                            Confidence: <span className="text-white">{confidence}%</span>
                        </div>

                        <p className="text-lg text-gray-200 font-medium leading-relaxed max-w-lg">
                            "{verdict.headline_reasoning}"
                        </p>
                    </GlassCard>
                </div>

                {/* BACK FACE WRAPPER */}
                <div
                    className="absolute inset-0 w-full h-full"
                    style={{
                        backfaceVisibility: 'hidden',
                        WebkitBackfaceVisibility: 'hidden',
                        transform: 'rotateY(180deg)',
                        zIndex: isFlipped ? 10 : 0,
                    }}
                >
                    <GlassCard
                        className="w-full h-full flex flex-col p-8 border-x border-b border-t-4 border-t-indigo-500 border-white/10 hover:border-white/20 cursor-pointer overflow-hidden backdrop-blur-xl bg-gradient-to-b from-indigo-900/30 to-slate-900/90"
                        onClick={() => setIsFlipped(false)}
                    >
                        <div className="flex items-center justify-between mb-8 border-b border-white/10 pb-4">
                            <div className="flex items-center gap-2">
                                 <FileText size={18} className="text-indigo-400"/>
                                 <h3 className="font-bold text-white text-lg">Deep Dive Analysis</h3>
                            </div>
                            <span className="text-xs text-indigo-400 bg-indigo-500/10 px-2 py-1 rounded border border-indigo-500/20">
                                AI Reasoning
                            </span>
                        </div>

                        <div className="flex-1 overflow-y-auto custom-scrollbar prose prose-invert prose-sm max-w-none prose-p:text-gray-300">
                             <ReactMarkdown>{verdict.deep_dive_justification}</ReactMarkdown>
                        </div>

                        {verdict.key_citations && verdict.key_citations.length > 0 && (
                            <div className="mt-6 pt-4 border-t border-white/10">
                                <div className="text-xs font-semibold text-gray-500 mb-2 uppercase">Key Citations</div>
                                <div className="flex flex-wrap gap-2">
                                    {verdict.key_citations.map((cite, i) => (
                                        <span key={i} className="text-xs text-blue-300 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
                                            {cite}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        <div className="absolute bottom-4 right-4 text-xs text-gray-500 flex items-center gap-1">
                           <RefreshCw size={12} /> Flip back
                       </div>
                    </GlassCard>
                </div>
            </motion.div>
        </div>
    );
}
