'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
    Check, Upload, FileText, Leaf, BarChart3, 
    Building2, Loader2, ChevronRight, X, ArrowLeft,
    RefreshCw, Info, ExternalLink, Trash2
} from 'lucide-react';
import { GlassModal, GlassModalFooter } from '@/components/ui/GlassModal';
import { GlassButton } from '@/components/ui/GlassButton';
import { GlassCard } from '@/components/ui/GlassCard';
import { cn } from '@/lib/utils';
import CompanyDocumentUpload from '@/components/documents/CompanyDocumentUpload';
import { analysisApi, AnalysisReport } from '@/lib/api/analysis';
import ReactMarkdown from 'react-markdown';

// --- Types ---

type AnalysisStep = 'topic' | 'upload' | 'progress' | 'results';
type AnalysisTopic = 'esg' | 'financials' | 'general';
type AnalysisStatus = 'waiting' | 'loading' | 'completed';

interface AnalysisWizardModalProps {
    isOpen: boolean;
    onClose: () => void;
    onComplete: () => void; // New prop for signaling completion
    companyName: string;
    companyId: string;
}

// --- Mock Data ---

// --- Mock Data Removed ---

// --- Sub-Components ---

// 1. Topic Selection
const TopicSelectionStep = ({ 
    selected, 
    onSelect, 
    onNext, 
    onCancel 
}: { 
    selected: AnalysisTopic | null, 
    onSelect: (t: AnalysisTopic) => void, 
    onNext: () => void,
    onCancel: () => void
}) => {
    return (
        <div className="space-y-6">
            <div className="grid gap-4">
                <button
                    onClick={() => onSelect('esg')}
                    className={cn(
                        "flex items-center gap-4 p-4 rounded-xl border transition-all text-left group relative overflow-hidden",
                        selected === 'esg' 
                            ? "bg-emerald-500/10 border-emerald-500/50" 
                            : "bg-white/5 border-white/10 hover:bg-white/[0.07] hover:border-white/20"
                    )}
                >
                    <div className={cn(
                        "w-12 h-12 rounded-lg flex items-center justify-center transition-colors",
                        selected === 'esg' ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/20" : "bg-white/5 text-gray-400 group-hover:text-emerald-400"
                    )}>
                        <Leaf size={24} />
                    </div>
                    <div className="flex-1">
                        <div className="font-semibold text-white flex items-center justify-between">
                            ESG
                            {selected === 'esg' && <Check size={18} className="text-emerald-500" />}
                        </div>
                        <div className="text-sm text-gray-400 mt-1">Environmental, Social & Governance analysis</div>
                    </div>
                    {selected === 'esg' && (
                        <motion.div 
                            layoutId="outline"
                            className="absolute inset-0 border-2 border-emerald-500 rounded-xl" 
                            initial={false}
                            transition={{ type: "spring", stiffness: 500, damping: 30 }}
                        />
                    )}
                </button>

                <button
                    onClick={() => onSelect('financials')}
                    className={cn(
                        "flex items-center gap-4 p-4 rounded-xl border transition-all text-left group relative overflow-hidden",
                        selected === 'financials' 
                            ? "bg-indigo-500/10 border-indigo-500/50" 
                            : "bg-white/5 border-white/10 hover:bg-white/[0.07] hover:border-white/20"
                    )}
                >
                    <div className={cn(
                        "w-12 h-12 rounded-lg flex items-center justify-center transition-colors",
                        selected === 'financials' ? "bg-indigo-500 text-white shadow-lg shadow-indigo-500/20" : "bg-white/5 text-gray-400 group-hover:text-indigo-400"
                    )}>
                        <BarChart3 size={24} />
                    </div>
                    <div className="flex-1">
                        <div className="font-semibold text-white flex items-center justify-between">
                            Financials
                            {selected === 'financials' && <Check size={18} className="text-indigo-500" />}
                        </div>
                        <div className="text-sm text-gray-400 mt-1">Financial performance & metrics</div>
                    </div>
                    {selected === 'financials' && (
                        <motion.div 
                            layoutId="outline"
                            className="absolute inset-0 border-2 border-indigo-500 rounded-xl" 
                            initial={false}
                            transition={{ type: "spring", stiffness: 500, damping: 30 }}
                        />
                    )}
                </button>

                <button
                    onClick={() => onSelect('general')}
                    className={cn(
                        "flex items-center gap-4 p-4 rounded-xl border transition-all text-left group relative overflow-hidden",
                        selected === 'general' 
                            ? "bg-blue-500/10 border-blue-500/50" 
                            : "bg-white/5 border-white/10 hover:bg-white/[0.07] hover:border-white/20"
                    )}
                >
                    <div className={cn(
                        "w-12 h-12 rounded-lg flex items-center justify-center transition-colors",
                        selected === 'general' ? "bg-blue-500 text-white shadow-lg shadow-blue-500/20" : "bg-white/5 text-gray-400 group-hover:text-blue-400"
                    )}>
                        <Building2 size={24} />
                    </div>
                    <div className="flex-1">
                        <div className="font-semibold text-white flex items-center justify-between">
                            General
                            {selected === 'general' && <Check size={18} className="text-blue-500" />}
                        </div>
                        <div className="text-sm text-gray-400 mt-1">Comprehensive company overview</div>
                    </div>
                    {selected === 'general' && (
                        <motion.div 
                            layoutId="outline"
                            className="absolute inset-0 border-2 border-blue-500 rounded-xl" 
                            initial={false}
                            transition={{ type: "spring", stiffness: 500, damping: 30 }}
                        />
                    )}
                </button>
            </div>

            <GlassModalFooter>
                <GlassButton variant="ghost" onClick={onCancel}>Cancel</GlassButton>
                <GlassButton onClick={onNext} disabled={!selected}>Next</GlassButton>
            </GlassModalFooter>
        </div>
    );
};

// 2. File Upload
const FileUploadStep = ({ onNext, onBack, onCancel, companyId }: { onNext: () => void, onBack: () => void, onCancel: () => void, companyId: string }) => {
    // We can track upload count via callback if needed, but for now we trust the user to proceed
    const [uploadCount, setUploadCount] = useState(0);

    return (
        <div className="space-y-6">
            <div className="h-96 overflow-y-auto pr-2 custom-scrollbar">
                <CompanyDocumentUpload 
                    companyId={companyId} 
                    onUploadSuccess={() => setUploadCount(prev => prev + 1)}
                />
            </div>

            <GlassModalFooter className="justify-between">
                <GlassButton variant="ghost" onClick={onBack} leftIcon={<ArrowLeft size={16}/>}>Back</GlassButton>
                <div className="flex gap-2">
                    <GlassButton variant="ghost" onClick={onCancel}>Cancel</GlassButton>
                    <GlassButton 
                        onClick={onNext} 
                    >
                        {uploadCount > 0 ? `Continue (${uploadCount} uploaded)` : 'Continue'}
                    </GlassButton>
                </div>
            </GlassModalFooter>
        </div>
    );
};

// 3. Progress
const ProgressStep = ({ onComplete, companyId }: { onComplete: () => void, companyId: string }) => {
    const [stepIndex, setStepIndex] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const steps = [
        { label: "Initializing", sub: "Starting analysis engine" },
        { label: "Pulling Data", sub: "Gathering news and documents" },
        { label: "Synthesizing", sub: "Generating insights with AI" },
        { label: "Finalizing", sub: "Formatting report" }
    ];

    const hasTriggered = useRef(false);

    // 1. Trigger Effect (Runs once)
    useEffect(() => {
        const trigger = async () => {
            if (hasTriggered.current) return;
            hasTriggered.current = true;
            
            try {
                console.log("Triggering analysis for:", companyId);
                await analysisApi.triggerAnalysis(companyId);
            } catch (e) {
                console.error("Trigger error:", e);
                setError("Failed to start analysis.");
            }
        };
        trigger();
    }, [companyId]);

    // 2. Polling & Visual Effect (Resilient to remounts)
    useEffect(() => {
        let isMounted = true;
        let pollInterval: NodeJS.Timeout;
        let visualInterval: NodeJS.Timeout;

        const startPolling = () => {
            const startTime = Date.now();
            const TIMEOUT = 300000; // 5 min timeout

            pollInterval = setInterval(async () => {
                if (!isMounted) return;

                try {
                    const reports = await analysisApi.getReports(companyId);
                    if (reports && reports.length > 0) {
                            const latest = reports[0];
                            console.log("Report found:", latest.id);
                            clearInterval(pollInterval);
                            setStepIndex(steps.length); // Complete all steps
                            setTimeout(onComplete, 800);
                    }
                } catch (e) {
                        console.error("Polling error:", e);
                }

                if (Date.now() - startTime > TIMEOUT) {
                    clearInterval(pollInterval);
                    if (isMounted) setError("Analysis timed out. Please try again.");
                }
            }, 2000);
        };

        startPolling();

        // Visual timer generic loop
        visualInterval = setInterval(() => {
                setStepIndex(prev => {
                    if (prev >= steps.length - 2) return prev; // Stuck at "Synthesizing" until done
                    return prev + 1;
                });
        }, 3000);

        return () => {
            isMounted = false;
            clearInterval(pollInterval);
            clearInterval(visualInterval);
        };
    }, [companyId, onComplete]);

    if (error) {
        return (
            <div className="py-12 text-center space-y-4">
                <div className="text-red-400 text-xl font-bold">Analysis Failed</div>
                <p className="text-gray-400">{error}</p>
                <GlassButton onClick={onComplete}>Close</GlassButton>
            </div>
        );
    }


    return (
        <div className="py-8 space-y-10">
            <div className="text-center space-y-2">
                <h2 className="text-2xl font-bold text-white">Analyzing Company</h2>
                <p className="text-gray-400">Please wait while we process your documents</p>
            </div>

            <div className="max-w-md mx-auto relative px-8">
                 {/* Vertical line connection */}
                 <div className="absolute left-[47px] top-4 bottom-4 w-0.5 bg-white/10" />
                 
                 <div className="space-y-6 relative z-10">
                    {steps.map((step, idx) => {
                        const isCompleted = stepIndex > idx;
                        const isCurrent = stepIndex === idx;
                        
                        return (
                            <motion.div 
                                key={idx}
                                initial={{ opacity: 0.5, x: -10 }}
                                animate={{ opacity: isCurrent || isCompleted ? 1 : 0.4, x: 0 }}
                                className="flex items-center gap-4"
                            >
                                <div className={cn(
                                    "w-8 h-8 rounded-full flex items-center justify-center transition-all duration-500 border-2",
                                    isCompleted 
                                        ? "bg-emerald-500 border-emerald-500 text-white"
                                        : isCurrent
                                            ? "bg-emerald-500/20 border-emerald-500 text-emerald-500"
                                            : "bg-black/20 border-white/10 text-transparent"
                                )}>
                                    {isCompleted ? <Check size={16} /> : <div className={cn("w-2 h-2 rounded-full", isCurrent && "bg-current")} />}
                                </div>
                                <div>
                                    <div className={cn("font-medium transition-colors", isCurrent ? "text-white" : "text-gray-400")}>{step.label}</div>
                                    {isCurrent && (
                                        <div className="text-xs text-emerald-400 mt-0.5">{step.sub}</div>
                                    )}
                                </div>
                            </motion.div>
                        );
                    })}
                 </div>
            </div>
            
            {/* Progress bar at bottom */}
            <div className="h-1 bg-white/10 rounded-full overflow-hidden w-full max-w-sm mx-auto">
                <motion.div 
                    className="h-full bg-emerald-500"
                    initial={{ width: "0%" }}
                    animate={{ width: `${((stepIndex + 1) / steps.length) * 100}%` }}
                    transition={{ duration: 0.5 }}
                />
            </div>
            <div className="text-center text-xs text-gray-500">Step {Math.min(stepIndex + 1, steps.length)} of {steps.length}</div>
        </div>
    );
};

// 4. Results
// --- Types ---


// 5. Financial Analysis View
export const FinancialAnalysisView = ({ report }: { report: AnalysisReport }) => {
    const financial = report.financial_analysis || {};
    const valuation = financial.valuation || { score: 0, summary: "No data", citations: [], sources: [] };
    const profitability = financial.profitability || { score: 0, summary: "No data", citations: [], sources: [] };
    const growth = financial.growth || { score: 0, summary: "No data", citations: [], sources: [] };
    const health = financial.health || { score: 0, summary: "No data", citations: [], sources: [] };

    const cards = [
        { id: 'valuation', title: "Valuation", data: valuation, border: 'border-l-blue-500/50', bg: 'bg-blue-500/20', iconColor: 'text-blue-400' },
        { id: 'profitability', title: "Profitability", data: profitability, border: 'border-l-amber-500/50', bg: 'bg-amber-500/20', iconColor: 'text-amber-400' },
        { id: 'growth', title: "Growth", data: growth, border: 'border-l-emerald-500/50', bg: 'bg-emerald-500/20', iconColor: 'text-emerald-400' },
        { id: 'health', title: "Financial Health", data: health, border: 'border-l-indigo-500/50', bg: 'bg-indigo-500/20', iconColor: 'text-indigo-400' },
    ];

    const getScoreColor = (score: number) => {
        if (score >= 80) return "text-emerald-500 bg-emerald-500/10 border-emerald-500/20";
        if (score >= 60) return "text-amber-500 bg-amber-500/10 border-amber-500/20";
        return "text-red-500 bg-red-500/10 border-red-500/20";
    };

    return (
        <div className="space-y-6">
             <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                 {cards.map(card => (
                     <div key={card.id} className="min-h-[220px]">
                        <GlassCard className={cn("h-full flex flex-col hover:border-white/20 transition-all border-l-2", card.border)}>
                            <div className="flex justify-between items-start mb-4">
                                 <div className="flex items-center gap-3">
                                    <div className={cn("w-9 h-9 rounded-lg flex items-center justify-center", card.bg)}>
                                        <BarChart3 size={18} className={card.iconColor} />
                                    </div>
                                    <h3 className="font-bold text-white text-lg">{card.title}</h3>
                                 </div>
                                 <div className={cn("px-2 py-1 rounded-lg text-xs font-bold border", getScoreColor(card.data.score))}>
                                     {card.data.score}%
                                 </div>
                            </div>

                            <div className="text-sm text-gray-300 leading-relaxed mb-4 flex-1 prose prose-invert prose-sm max-w-none overflow-y-auto custom-scrollbar prose-p:text-gray-300 prose-strong:text-white">
                                <ReactMarkdown components={citationComponents}>{formatText(card.data.summary)}</ReactMarkdown>
                            </div>
                            
                            {/* Highlights Section */}
                            {card.data.highlights && card.data.highlights.length > 0 && (
                                <div className="flex flex-wrap gap-2 mb-4">
                                    {card.data.highlights.map((h: string, idx: number) => (
                                        <span key={idx} className="text-[10px] font-semibold px-2 py-1 rounded bg-white/10 text-white border border-white/5">
                                            {h}
                                        </span>
                                    ))}
                                </div>
                            )}

                            <div className="mt-auto border-t border-white/10 pt-4">
                                <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
                                    <FileText size={12}/> Sources
                                </div>
                                {card.data.sources.map((source, i) => (
                                    <div key={i} className="text-xs text-indigo-300 truncate hover:text-indigo-200">
                                        [{i+1}] {source}
                                    </div>
                                ))}
                            </div>
                        </GlassCard>
                     </div>
                 ))}
            </div>
        </div>
    );
};

// ... (TopicSelectionStep, FileUploadStep, ProgressStep remain unchanged) ...

// 4. Results

// --- Helpers ---
const formatText = (text: string | null | undefined) => {
    if (!text) return "";
    return text.replace(/\[(\d+)\]/g, '[$&](#source-$1)');
};

const citationComponents = {
    a: ({ href, children, ...props }: any) => {
        if (href && href.startsWith('#source-')) {
            return (
                <span className="text-cyan-400 font-bold mx-0.5 cursor-help hover:underline decoration-dash" title="Citation Source">
                    {children}
                </span>
            );
        }
        return <a href={href} className="text-blue-400 hover:underline" {...props}>{children}</a>;
    }
};

export const AnalysisResultsView = ({ report, onReanalyze, onDelete }: { report: AnalysisReport, onReanalyze: () => void, onDelete?: () => void }) => {
    // Card State Management
    const [flippedCard, setFlippedCard] = useState<string | null>(null);
    const [showDetails, setShowDetails] = useState(false); // Toggle for top 3 cards
    const [viewMode, setViewMode] = useState<'esg' | 'financial'>('esg'); // Tab state

    const toggleFlip = (cardId: string) => {
        setFlippedCard(prev => prev === cardId ? null : cardId);
    };



    // Safely access esg_analysis from report
    const esg = report.esg_analysis || {};
    const overview = esg.overview || { score: 0, summary: "No data", citations: [], sources: [] };
    const governance = esg.governance || { score: 0, summary: "No data", citations: [], sources: [] };
    const environmental = esg.environmental || { score: 0, summary: "No data", citations: [], sources: [] };
    const social = esg.social || { score: 0, summary: "No data", citations: [], sources: [] };
    const disclosure = esg.disclosure || { score: 0, summary: "No data", citations: [], sources: [] };

    const cards = [
        { id: 'overview', title: "Overview", data: overview, color: "text-emerald-400" },
        { id: 'governance', title: "Governance & ESG Integration", data: governance, color: "text-amber-400" },
        { id: 'environmental', title: "Environmental", data: environmental, color: "text-emerald-400" },
        { id: 'social', title: "Social", data: social, color: "text-amber-400" },
        { id: 'disclosure', title: "Disclosure Quality", data: disclosure, color: "text-emerald-400" },
    ];

    const getScoreColor = (score: number) => {
        if (score >= 80) return "text-emerald-500 bg-emerald-500/10 border-emerald-500/20";
        if (score >= 60) return "text-amber-500 bg-amber-500/10 border-amber-500/20";
        return "text-red-500 bg-red-500/10 border-red-500/20";
    };

    return (
        <GlassCard className="space-y-6 mt-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                     <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                        Analysis Results
                     </h2>
                     <p className="text-gray-400 mt-1">Comprehensive assessment based on uploaded documents and external sources</p>
                </div>
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-3 px-4 py-2 rounded-xl bg-white/5 border border-white/10">
                        <span className="text-sm text-gray-400">Overall Confidence</span>
                        <span className="text-lg font-bold text-emerald-400">{report.confidence_score}%</span>
                    </div>
                    {/* View Switcher */}
                    <div className="flex bg-white/5 p-1 rounded-lg border border-white/10">
                        <button 
                            onClick={() => setViewMode('esg')}
                            className={cn(
                                "px-3 py-1.5 rounded-md text-sm font-medium transition-all",
                                viewMode === 'esg' ? "bg-emerald-500 text-white shadow-lg" : "text-gray-400 hover:text-white"
                            )}
                        >
                            ESG
                        </button>
                        <button 
                            onClick={() => setViewMode('financial')}
                            className={cn(
                                "px-3 py-1.5 rounded-md text-sm font-medium transition-all",
                                viewMode === 'financial' ? "bg-indigo-500 text-white shadow-lg" : "text-gray-400 hover:text-white"
                            )}
                        >
                            Financials
                        </button>
                    </div>
                    
                    {onDelete && (
                         <button
                            onClick={onDelete}
                            className="p-2 rounded-lg bg-white/5 hover:bg-red-500/10 hover:text-red-400 text-gray-400 transition-colors border border-white/10"
                            title="Delete this report"
                        >
                            <Trash2 size={18} />
                        </button>
                    )}

                    <GlassButton 
                        size="sm"
                        variant="ghost"
                        onClick={() => setShowDetails(!showDetails)}
                        leftIcon={<Info size={16}/>}
                    >
                        {showDetails ? "Hide Details" : "View Breakdown"}
                    </GlassButton>
                </div>
            </div>

            {/* Analysis Overview Section - Toggled */}
            <AnimatePresence>
                {showDetails && !flippedCard && (
                    <motion.div 
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="overflow-hidden"
                    >
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pb-2">
                             <GlassCard className="space-y-4 border-l-2 border-l-blue-500/50">
                                 <div className="flex items-center gap-2">
                                     <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center">
                                         <FileText size={16} className="text-blue-400" />
                                     </div>
                                     <h3 className="font-semibold text-white">Investment Summary</h3>
                                 </div>
                                 <div className="text-sm text-gray-300 leading-relaxed prose prose-invert prose-sm max-w-none max-h-[300px] overflow-y-auto custom-scrollbar prose-p:text-gray-300 prose-strong:text-white">
                                    <ReactMarkdown>{report.summary}</ReactMarkdown>
                                 </div>
                             </GlassCard>
                             <GlassCard className="space-y-4 border-l-2 border-l-emerald-500/50">
                                 <div className="flex items-center gap-2">
                                     <div className="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                                         <BarChart3 size={16} className="text-emerald-400" />
                                     </div>
                                     <h3 className="font-semibold text-white">Bull Case (Claims)</h3>
                                 </div>
                                 <div className="text-sm text-gray-300 leading-relaxed prose prose-invert prose-sm max-w-none max-h-[300px] overflow-y-auto custom-scrollbar prose-p:text-gray-300 prose-strong:text-white prose-li:text-gray-300">
                                    <ReactMarkdown>{report.bull_case}</ReactMarkdown>
                                 </div>
                             </GlassCard>
                             <GlassCard className="space-y-4 border-l-2 border-l-amber-500/50">
                                 <div className="flex items-center gap-2">
                                     <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center">
                                         <Info size={16} className="text-amber-400" />
                                     </div>
                                     <h3 className="font-semibold text-white">Risks & Concerns</h3>
                                 </div>
                                 <div className="text-sm text-gray-300 leading-relaxed prose prose-invert prose-sm max-w-none max-h-[300px] overflow-y-auto custom-scrollbar prose-p:text-gray-300 prose-strong:text-white prose-li:text-gray-300 prose-li:marker:text-amber-400">
                                    <ReactMarkdown>{report.risk_factors}</ReactMarkdown>
                                 </div>
                             </GlassCard>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
            
            {/* Legend */}
             <div className="flex items-center justify-center gap-6 text-xs text-gray-500 pt-2 pb-4">
                 <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-emerald-500"/> High Confidence (80%+)</div>
                 <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-amber-500"/> Medium Confidence (60-79%)</div>
                 <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-red-500"/> Low Confidence (60%)</div>
             </div>


             
             {viewMode === 'financial' ? (
                 <FinancialAnalysisView report={report} />
             ) : (
                <>
                {/* ESG Overview Card - Full Width */}
                {(() => {
                    const overviewCard = cards.find(c => c.id === 'overview')!;
                    const isFlipped = flippedCard === overviewCard.id;
                    return (
                        <div
                            className={cn(
                                "relative perspective-1000 transition-all duration-500",
                                isFlipped ? "min-h-[400px]" : "min-h-[220px]"
                            )}
                        >
                            <GlassCard
                                className="h-full cursor-pointer hover:border-white/20 transition-all group overflow-hidden flex flex-col border-l-2 border-l-emerald-500/50"
                                onClick={() => toggleFlip(overviewCard.id)}
                            >
                                <div className="flex justify-between items-start mb-4">
                                     <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                                            <Leaf size={20} className="text-emerald-400" />
                                        </div>
                                        <div>
                                            <span className="text-[10px] font-bold uppercase tracking-wider bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded">Main</span>
                                            <h3 className="font-bold text-white text-lg mt-1">{overviewCard.title}</h3>
                                        </div>
                                     </div>
                                     <div className={cn("px-3 py-1.5 rounded-lg text-sm font-bold border", getScoreColor(overviewCard.data.score))}>
                                         {overviewCard.data.score}%
                                     </div>
                                </div>

                                <div className={cn(
                                    "text-sm text-gray-300 leading-relaxed mb-4 flex-1 prose prose-invert prose-sm max-w-none prose-p:text-gray-300 prose-strong:text-white prose-li:text-gray-300",
                                    !isFlipped ? "line-clamp-5" : "max-h-[300px] overflow-y-auto custom-scrollbar"
                                )}>
                                    <ReactMarkdown components={citationComponents}>
                                        {formatText((isFlipped && overviewCard.data.detail) || overviewCard.data.summary)}
                                    </ReactMarkdown>
                                </div>

                                {/* Highlights Badge Section */}
                                {!isFlipped && overviewCard.data.highlights && overviewCard.data.highlights.length > 0 && (
                                    <div className="flex flex-wrap gap-2 mb-4">
                                        {(overviewCard.data.highlights || []).map((h: string, idx: number) => (
                                            <span key={idx} className="text-[10px] font-semibold px-2 py-1 rounded bg-white/10 text-white border border-white/5">
                                                {h}
                                            </span>
                                        ))}
                                    </div>
                                )}

                                <div className="mt-auto border-t border-white/10 pt-4">
                                    <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
                                        <FileText size={12}/> Sources
                                    </div>
                                    <div className="flex flex-wrap gap-4">
                                        {(overviewCard.data.sources || []).map((source, i) => (
                                            <div key={i} className="text-xs text-indigo-300 hover:text-indigo-200">
                                                [{i+1}] {source}
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div className="absolute bottom-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity text-xs text-gray-500 flex items-center gap-1">
                                    <RefreshCw size={12}/> {isFlipped ? "Close details" : "View analysis"}
                                </div>
                            </GlassCard>
                        </div>
                    );
                })()}
    
                {/* Other 4 Cards - 2x2 Grid */}
                <div className={cn(
                    "grid gap-4 transition-all duration-500",
                    flippedCard && flippedCard !== 'overview' ? "grid-cols-1" : "grid-cols-1 md:grid-cols-2"
                )}>
                     {cards.filter(c => c.id !== 'overview').map(card => {
                         if (flippedCard && flippedCard !== card.id) return null;

                         const isFlipped = flippedCard === card.id;
                        // Debug log
                        if (isFlipped) {
                             // console.log(`Card ${card.id} flipped. Report ID:`, report.id, 'Detail present:', !!card.data.detail, 'Length:', card.data.detail?.length);
                             console.log('Full data:', card.data);
                        }

                         // Get card-specific styling
                         const getCardStyle = (id: string) => {
                             switch(id) {
                                 case 'governance': return { border: 'border-l-amber-500/50', bg: 'bg-amber-500/20', text: 'text-amber-400', Icon: Building2 };
                                 case 'environmental': return { border: 'border-l-emerald-500/50', bg: 'bg-emerald-500/20', text: 'text-emerald-400', Icon: Leaf };
                                 case 'social': return { border: 'border-l-blue-500/50', bg: 'bg-blue-500/20', text: 'text-blue-400', Icon: Building2 };
                                 case 'disclosure': return { border: 'border-l-indigo-500/50', bg: 'bg-indigo-500/20', text: 'text-indigo-400', Icon: FileText };
                                 default: return { border: 'border-l-gray-500/50', bg: 'bg-gray-500/20', text: 'text-gray-400', Icon: Info };
                             }
                         };
                         const style = getCardStyle(card.id);

                         return (
                             <div
                                key={card.id}
                                className={cn(
                                    "relative perspective-1000 transition-all duration-500",
                                    isFlipped ? "md:col-span-2 min-h-[400px]" : "min-h-[220px]"
                                )}
                             >
                                <GlassCard
                                    className={cn("h-full cursor-pointer hover:border-white/20 transition-all group overflow-hidden flex flex-col border-l-2", style.border)}
                                    onClick={() => toggleFlip(card.id)}
                                >
                                    <div className="flex justify-between items-start mb-4">
                                         <div className="flex items-center gap-3">
                                            <div className={cn("w-9 h-9 rounded-lg flex items-center justify-center", style.bg)}>
                                                <style.Icon size={18} className={style.text} />
                                            </div>
                                            <h3 className="font-bold text-white text-lg">{card.title}</h3>
                                         </div>
                                         <div className={cn("px-2 py-1 rounded-lg text-xs font-bold border", getScoreColor(card.data.score))}>
                                             {card.data.score}%
                                         </div>
                                    </div>



                                    <div className={cn(
                                        "text-sm text-gray-300 leading-relaxed mb-4 flex-1 prose prose-invert prose-sm max-w-none prose-p:text-gray-300 prose-strong:text-white prose-li:text-gray-300",
                                        !isFlipped ? "line-clamp-4" : "max-h-[250px] overflow-y-auto custom-scrollbar"
                                    )}>
                                        <ReactMarkdown components={citationComponents}>
                                            {formatText((isFlipped && card.data.detail) || card.data.summary)}
                                        </ReactMarkdown>
                                    </div>

                                    {/* Highlights Badge Section */}
                                    {!isFlipped && card.data.highlights && card.data.highlights.length > 0 && (
                                        <div className="flex flex-wrap gap-2 mb-4">
                                            {card.data.highlights.map((h: string, idx: number) => (
                                                <span key={idx} className="text-[10px] font-semibold px-2 py-1 rounded bg-white/10 text-white border border-white/5 truncate max-w-full">
                                                    {h}
                                                </span>
                                            ))}
                                        </div>
                                    )}

                                    <div className="mt-auto border-t border-white/10 pt-4">
                                        <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
                                            <FileText size={12}/> Sources
                                        </div>
                                        {(card.data.sources || []).map((source, i) => (
                                            <div key={i} className="text-xs text-indigo-300 truncate hover:text-indigo-200">
                                                [{i+1}] {source}
                                            </div>
                                        ))}
                                    </div>

                                    <div className="absolute bottom-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity text-xs text-gray-500 flex items-center gap-1">
                                        <RefreshCw size={12}/> {isFlipped ? "Close details" : "View analysis"}
                                    </div>
                                </GlassCard>
                             </div>
                         );
                     })}
                </div>
                </>
             )}
            
            <div className="text-center text-xs text-gray-600 mt-8">
                Click on any card to flip and see the detailed analysis backing
            </div>
        </GlassCard>
    );
};


// --- Main Wizard Component ---

export function AnalysisWizardModal({ isOpen, onClose, onComplete, companyName, companyId }: AnalysisWizardModalProps) {
    const [step, setStep] = useState<AnalysisStep>('topic');
    const [topic, setTopic] = useState<AnalysisTopic | null>(null);

    // Reset when closed
    useEffect(() => {
        if (!isOpen) {
            // small delay to reset after animation
            setTimeout(() => {
                setStep('topic');
                setTopic(null);
            }, 300);
        }
    }, [isOpen]);

    const getTitle = () => {
        switch(step) {
            case 'topic': return "Select Analysis Type";
            case 'upload': return "Upload Documents";
            case 'progress': return ""; // Custom header in component
            case 'results': return "";  // Custom header in component
            default: return "Analysis";
        }
    };

    const getDescription = () => {
        switch(step) {
            case 'topic': return "Choose the type of analysis you want to perform";
            case 'upload': return `Upload PDF files for ${topic ? topic.toUpperCase() : ''} analysis`;
            default: return undefined;
        }
    };

    const getSize = () => {
        if (step === 'results') return 'full';
        if (step === 'progress') return 'lg';
        return 'md';
    }

    return (
        <GlassModal
            isOpen={isOpen}
            onClose={onClose}
            title={getTitle()}
            description={getDescription()}
            size={getSize()}
            // Hide default close button for progress/results if needed, keeping consistent for now
            showCloseButton={step !== 'progress'}
            closeOnOverlayClick={step !== 'progress'}
        >
            <AnimatePresence mode="wait">
                {step === 'topic' && (
                    <motion.div 
                        key="topic"
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                    >
                        <TopicSelectionStep 
                            selected={topic}
                            onSelect={setTopic}
                            onNext={() => setStep('upload')}
                            onCancel={onClose}
                        />
                    </motion.div>
                )}

                {step === 'upload' && (
                    <motion.div 
                        key="upload"
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                    >
                        <FileUploadStep 
                            companyId={companyId}
                            onNext={() => setStep('progress')}
                            onBack={() => setStep('topic')}
                            onCancel={onClose}
                        />
                    </motion.div>
                )}

                {step === 'progress' && (
                    <motion.div 
                        key="progress"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                    >
                        <ProgressStep 
                            companyId={companyId}
                            onComplete={() => {
                                onClose();
                                onComplete();
                                setTimeout(() => {
                                    setStep('topic');
                                    setTopic(null);
                                }, 500); 
                            }}
                        />
                    </motion.div>
                )}

                {/* Results Step Removed from Modal - handled externally */}
            </AnimatePresence>
        </GlassModal>
    );
}

export default AnalysisWizardModal;
