'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Check, Upload, FileText, Leaf, BarChart3,
    Building2, Loader2, ChevronRight, X, ArrowLeft,
    RefreshCw, Info, ExternalLink, Trash2, Scale,
    TrendingUp, TrendingDown, AlertTriangle, Shield,
    Users, Eye, Award, Gavel, MessageSquare
} from 'lucide-react';
import { GlassModal, GlassModalFooter } from '@/components/ui/GlassModal';
import { GlassButton } from '@/components/ui/GlassButton';
import { GlassCard } from '@/components/ui/GlassCard';
import { cn } from '@/lib/utils';
import CompanyDocumentUpload from '@/components/documents/CompanyDocumentUpload';
import {
    analysisApi,
    AnalysisReport,
    AnalysisJobStatusResponse,
    SectionContent,
    SourceMetadata,
    getDebateReport,
    getCitationRegistry,
    getRoleBasedInsight,
    getMarketSentiment
} from '@/lib/api/analysis';
import ReactMarkdown from 'react-markdown';

// --- Types ---

type AnalysisStep = 'topic' | 'upload' | 'progress' | 'results';
type AnalysisTopic = 'esg' | 'financials' | 'general';
type AnalysisStatus = 'waiting' | 'loading' | 'completed';

interface AnalysisWizardModalProps {
    isOpen: boolean;
    onClose: () => void;
    onComplete: () => void;
    companyName: string;
    companyId: string;
}

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
const FileUploadStep = ({ onNext, onBack, onCancel, companyId, companyName }: { onNext: () => void, onBack: () => void, onCancel: () => void, companyId: string, companyName?: string }) => {
    const [uploadCount, setUploadCount] = useState(0);

    return (
        <div className="space-y-6">
            <div className="h-96 overflow-y-auto pr-2 custom-scrollbar">
                <CompanyDocumentUpload
                    companyId={companyId}
                    companyTicker={companyName}
                    onUploadSuccess={() => setUploadCount(prev => prev + 1)}
                />
            </div>

            <GlassModalFooter className="justify-between">
                <GlassButton variant="ghost" onClick={onBack} leftIcon={<ArrowLeft size={16}/>}>Back</GlassButton>
                <div className="flex gap-2">
                    <GlassButton variant="ghost" onClick={onCancel}>Cancel</GlassButton>
                    <GlassButton onClick={onNext}>
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
    const [currentStep, setCurrentStep] = useState<string>("Starting analysis engine");
    const [progress, setProgress] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const steps = [
        { label: "Initializing", sub: "Starting analysis engine" },
        { label: "Gathering Intel", sub: "Analyzing news, financials & documents" },
        { label: "Cross-Examination", sub: "Agents debating findings" },
        { label: "Synthesizing", sub: "Generating final report" },
        { label: "Finalizing", sub: "Embedding for search" }
    ];

    const hasTriggered = useRef(false);

    const statusToStep = (status: string): number => {
        switch (status) {
            case 'PENDING': return 0;
            case 'GATHERING_INTEL': return 1;
            case 'CROSS_EXAMINATION': return 2;
            case 'SYNTHESIZING': return 3;
            case 'EMBEDDING': return 4;
            case 'COMPLETED': return 5;
            default: return 0;
        }
    };

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

    useEffect(() => {
        let isMounted = true;
        let pollInterval: NodeJS.Timeout;

        const startPolling = () => {
            const startTime = Date.now();
            const TIMEOUT = 600000;

            pollInterval = setInterval(async () => {
                if (!isMounted) return;

                try {
                    const statusResponse: AnalysisJobStatusResponse = await analysisApi.getStatus(companyId);

                    if (statusResponse.status === 'COMPLETED') {
                        console.log("Analysis completed, report:", statusResponse.report_id);
                        clearInterval(pollInterval);
                        setStepIndex(steps.length);
                        setProgress(100);
                        setTimeout(onComplete, 800);
                        return;
                    }

                    if (statusResponse.status === 'FAILED') {
                        clearInterval(pollInterval);
                        if (isMounted) {
                            setError(statusResponse.error_message || "Analysis failed. Please try again.");
                        }
                        return;
                    }

                    if (statusResponse.progress !== undefined) {
                        setProgress(statusResponse.progress);
                    }
                    if (statusResponse.current_step) {
                        setCurrentStep(statusResponse.current_step);
                    }
                    setStepIndex(statusToStep(statusResponse.status));

                } catch (e) {
                    console.error("Status polling error:", e);
                    try {
                        const reports = await analysisApi.getReports(companyId);
                        if (reports && reports.length > 0) {
                            console.log("Report found via fallback:", reports[0].id);
                            clearInterval(pollInterval);
                            setStepIndex(steps.length);
                            setTimeout(onComplete, 800);
                            return;
                        }
                    } catch {
                        // Ignore fallback errors
                    }
                }

                if (Date.now() - startTime > TIMEOUT) {
                    clearInterval(pollInterval);
                    if (isMounted) setError("Analysis timed out. The analysis may still be running - please check back later.");
                }
            }, 2000);
        };

        startPolling();

        return () => {
            isMounted = false;
            clearInterval(pollInterval);
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
                <p className="text-gray-400">{currentStep}</p>
            </div>

            <div className="max-w-md mx-auto relative px-8">
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

            <div className="h-1 bg-white/10 rounded-full overflow-hidden w-full max-w-sm mx-auto">
                <motion.div
                    className="h-full bg-emerald-500"
                    initial={{ width: "0%" }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.5 }}
                />
            </div>
            <div className="text-center text-xs text-gray-500">{progress}% complete</div>
        </div>
    );
};

// =============================================================================
// CITATION-AWARE COMPONENTS
// =============================================================================

// Citation rendering component with tooltip
const CitationLink = ({
    citationId,
    registry
}: {
    citationId: string;
    registry: Record<string, SourceMetadata>;
}) => {
    const source = registry[citationId];

    if (!source) {
        return <span className="text-red-400 font-bold mx-0.5">[{citationId}?]</span>;
    }

    const getTypeColor = () => {
        switch (source.type) {
            case 'News': return 'text-cyan-400 hover:text-cyan-300';
            case 'Financial': return 'text-amber-400 hover:text-amber-300';
            case 'Document': return 'text-purple-400 hover:text-purple-300';
            default: return 'text-gray-400';
        }
    };

    const getTooltip = () => {
        let tooltip = source.title;
        if (source.date) tooltip += ` (${source.date})`;
        if (source.page_number) tooltip += ` - Page ${source.page_number}`;
        return tooltip;
    };

    const isClickable = source.url_or_path &&
        (source.url_or_path.startsWith('http') || source.url_or_path.startsWith('/') || source.type === 'News');


    if (isClickable) {
        // Append token if it's a relative path (document download)
        let href = source.url_or_path;
        if (source.url_or_path?.startsWith('/') && typeof window !== 'undefined') {
            const token = localStorage.getItem('token');
            if (token) {
                const separator = href?.includes('?') ? '&' : '?';
                href = `${href}${separator}token=${token}`;
            }
        }

        return (
            <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className={cn("font-bold mx-0.5 cursor-pointer underline decoration-dotted", getTypeColor())}
                title={getTooltip()}
            >
                [{citationId}]
            </a>
        );
    }

    return (
        <span
            className={cn("font-bold mx-0.5 cursor-help", getTypeColor())}
            title={getTooltip()}
        >
            [{citationId}]
        </span>
    );
};

// Markdown components with citation support
const createCitationComponents = (registry: Record<string, SourceMetadata>) => ({
    p: ({ children, ...props }: any) => {
        // Process text nodes to find citations
        const processChildren = (child: any): any => {
            if (typeof child === 'string') {
                // Split by citation pattern: [ID] or [ID, text] or [ID1, ID2]
                // Improved regex to capture content inside brackets
                const parts = child.split(/(\[[NFD]\d+(?:[^\]]*)\])/g);
                return parts.map((part: string, idx: number) => {
                    // Check if part is a citation block
                    if (part.startsWith('[') && part.endsWith(']')) {
                        // Remove brackets
                        const content = part.slice(1, -1);
                        
                        // Check if it's a list of IDs or ID+text
                        // We primarily look for the FIRST token as the ID
                        const tokens = content.split(',').map(t => t.trim());
                        
                        // Render logic
                        return (
                             <span key={idx} className="whitespace-nowrap">
                                <span className="text-gray-500 font-bold">[</span>
                                {tokens.map((token, i) => {
                                    // Check if token looks like an ID (N1, F1, D1)
                                    const idMatch = token.match(/^([NFD]\d+)(.*)$/);
                                    
                                    if (idMatch) {
                                        const id = idMatch[1];
                                        const suffix = idMatch[2]; // e.g. " Page 18" if passed as one token, or separate if comma
                                        
                                        return (
                                            <span key={i}>
                                                {i > 0 && <span className="text-gray-500 font-bold">, </span>}
                                                <CitationLink citationId={id} registry={registry} />
                                                {suffix && <span className="text-gray-500 text-xs">{suffix}</span>}
                                            </span>
                                        );
                                    } else {
                                        // It's just text (e.g. "Page 18")
                                        return (
                                            <span key={i}>
                                                {i > 0 && <span className="text-gray-500 font-bold">, </span>}
                                                <span className="text-gray-500 text-xs font-semibold">{token}</span>
                                            </span>
                                        );
                                    }
                                })}
                                <span className="text-gray-500 font-bold">]</span>
                            </span>
                        );
                    }
                    return part;
                });
            }
            return child;
        };

        const processedChildren = Array.isArray(children)
            ? children.map((child: any, idx: number) => <span key={idx}>{processChildren(child)}</span>)
            : processChildren(children);

        return <p className="mb-2 last:mb-0" {...props}>{processedChildren}</p>;
    },
    ul: ({ children, ...props }: any) => <ul className="list-disc pl-5 my-2 space-y-1 text-gray-300" {...props}>{children}</ul>,
    ol: ({ children, ...props }: any) => <ol className="list-decimal pl-5 my-2 space-y-1 text-gray-300" {...props}>{children}</ol>,
    li: ({ children, ...props }: any) => {
        const processChildren = (child: any): any => {
           if (typeof child === 'string') {
                // Same logic as p tag
                const parts = child.split(/(\[[NFD]\d+(?:[^\]]*)\])/g);
                return parts.map((part: string, idx: number) => {
                    if (part.startsWith('[') && part.endsWith(']')) {
                        const content = part.slice(1, -1);
                        const tokens = content.split(',').map(t => t.trim());
                        
                        return (
                             <span key={idx} className="whitespace-nowrap">
                                <span className="text-gray-500 font-bold">[</span>
                                {tokens.map((token, i) => {
                                    const idMatch = token.match(/^([NFD]\d+)(.*)$/);
                                    if (idMatch) {
                                        const id = idMatch[1];
                                        const suffix = idMatch[2];
                                        return (
                                            <span key={i}>
                                                {i > 0 && <span className="text-gray-500 font-bold">, </span>}
                                                <CitationLink citationId={id} registry={registry} />
                                                {suffix && <span className="text-gray-500 text-xs">{suffix}</span>}
                                            </span>
                                        );
                                    } else {
                                        return (
                                            <span key={i}>
                                                {i > 0 && <span className="text-gray-500 font-bold">, </span>}
                                                <span className="text-gray-500 text-xs font-semibold">{token}</span>
                                            </span>
                                        );
                                    }
                                })}
                                <span className="text-gray-500 font-bold">]</span>
                            </span>
                        );
                    }
                    return part;
                });
            }
            return child;
        };

        const processedChildren = Array.isArray(children)
            ? children.map((child: any, idx: number) => <span key={idx}>{processChildren(child)}</span>)
            : processChildren(children);

        return <li {...props}>{processedChildren}</li>;
    },
    strong: ({ children, ...props }: any) => <strong className="font-bold text-white" {...props}>{children}</strong>,
    a: ({ href, children, ...props }: any) => {
        if (href && href.startsWith('#source-')) {
            return (
                <span className="text-cyan-400 font-bold mx-0.5 cursor-help hover:underline decoration-dotted" title="Citation Source">
                    {children}
                </span>
            );
        }
        return <a href={href} className="text-blue-400 hover:underline" target="_blank" rel="noopener noreferrer" {...props}>{children}</a>;
    }
});

// Helper to format text with citations
const formatTextWithCitations = (text: string | null | undefined): string => {
    if (!text) return "";
    return text;
};

// Helper to get score color
const getScoreColor = (score: number) => {
    if (score >= 80) return "text-emerald-500 bg-emerald-500/10 border-emerald-500/20";
    if (score >= 60) return "text-amber-500 bg-amber-500/10 border-amber-500/20";
    return "text-red-500 bg-red-500/10 border-red-500/20";
};

// Helper to get decision color and icon
const getDecisionStyle = (decision: string) => {
    const upperDecision = decision?.toUpperCase() || '';

    // Positive decisions
    if (['BUY', 'ENGAGE', 'APPROVE', 'APPROVE CREDIT', 'OVERWEIGHT'].includes(upperDecision)) {
        return { color: 'text-emerald-400', bg: 'bg-emerald-500/20', border: 'border-emerald-500/50', Icon: TrendingUp };
    }
    // Negative decisions
    if (['SELL', 'AVOID', 'REJECT', 'REJECT CREDIT', 'UNDERWEIGHT'].includes(upperDecision)) {
        return { color: 'text-red-400', bg: 'bg-red-500/20', border: 'border-red-500/50', Icon: TrendingDown };
    }
    // Neutral decisions
    return { color: 'text-amber-400', bg: 'bg-amber-500/20', border: 'border-amber-500/50', Icon: Scale };
};

// Get persona label
const getPersonaLabel = (persona: string | undefined) => {
    switch (persona) {
        case 'INVESTOR': return 'Investor';
        case 'RELATIONSHIP_MANAGER': return 'Relationship Manager';
        case 'CREDIT_RISK': return 'Credit Risk Analyst';
        case 'MARKET_ANALYST': return 'Market Analyst';
        default: return 'Investor';
    }
};

// =============================================================================
// SECTION CARD COMPONENT (Reusable for ESG and Financial)
// =============================================================================

interface SectionCardProps {
    id: string;
    title: string;
    data: SectionContent;
    icon: React.ElementType;
    borderColor: string;
    bgColor: string;
    textColor: string;
    isFlipped: boolean;
    onFlip: () => void;
    registry: Record<string, SourceMetadata>;
    isMain?: boolean;
}

const SectionCard = ({
    id, title, data, icon: Icon, borderColor, bgColor, textColor,
    isFlipped, onFlip, registry, isMain
}: SectionCardProps) => {
    const citationComponents = createCitationComponents(registry);

    // Extract sources from detailed_findings citations
    const extractSources = (): string[] => {
        const allText = [data.preview_summary, ...(data.detailed_findings || [])].join(' ');
        const matches = allText.match(/\[[NFD]\d+\]/g) || [];
        const uniqueIds = [...new Set(matches.map(m => m.replace(/[\[\]]/g, '')))];
        return uniqueIds.map(id => {
            const source = registry[id];
            return source ? `[${id}] ${source.title}` : `[${id}] Unknown`;
        }).slice(0, 5);
    };

    const sources = extractSources();

    return (
        <div className={cn(
            "relative perspective-1000 transition-all duration-500",
            isFlipped ? (isMain ? "min-h-[400px]" : "md:col-span-2 min-h-[400px]") : "min-h-[220px]"
        )}>
            <GlassCard
                className={cn(
                    "h-full cursor-pointer hover:border-white/20 transition-all group overflow-hidden flex flex-col border-l-2",
                    borderColor
                )}
                onClick={onFlip}
            >
                <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center gap-3">
                        <div className={cn("w-9 h-9 rounded-lg flex items-center justify-center", bgColor)}>
                            <Icon size={18} className={textColor} />
                        </div>
                        <div>
                            {isMain && (
                                <span className="text-[10px] font-bold uppercase tracking-wider bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded">Main</span>
                            )}
                            <h3 className={cn("font-bold text-white text-lg", isMain && "mt-1")}>{title}</h3>
                        </div>
                    </div>
                    <div className={cn("px-2 py-1 rounded-lg text-xs font-bold border", getScoreColor(data.confidence_score))}>
                        {data.confidence_score}%
                    </div>
                </div>

                <div className={cn(
                    "text-sm text-gray-300 leading-relaxed mb-4 flex-1 prose prose-invert prose-sm max-w-none prose-p:text-gray-300 prose-strong:text-white prose-li:text-gray-300",
                    !isFlipped ? "line-clamp-4" : "max-h-[250px] overflow-y-auto custom-scrollbar"
                )}>
                    {isFlipped && data.detailed_findings && data.detailed_findings.length > 0 ? (
                        <ul className="list-disc list-outside ml-4 space-y-2">
                            {data.detailed_findings.map((finding, idx) => (
                                <li key={idx} className="text-gray-300 pl-1">
                                    <ReactMarkdown 
                                        components={{
                                            ...citationComponents,
                                            p: 'span' // Prevent block-level paragraphs inside li
                                        }}
                                    >
                                        {finding}
                                    </ReactMarkdown>
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <ReactMarkdown components={citationComponents}>
                            {formatTextWithCitations(data.preview_summary)}
                        </ReactMarkdown>
                    )}
                </div>

                {/* Highlights */}
                {!isFlipped && data.highlights && data.highlights.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-4">
                        {data.highlights.slice(0, 4).map((h, idx) => (
                            <span key={idx} className="text-[10px] font-semibold px-2 py-1 rounded bg-white/10 text-white border border-white/5 truncate max-w-[200px]">
                                {h}
                            </span>
                        ))}
                    </div>
                )}

                {/* Sources */}
                <div className="mt-auto border-t border-white/10 pt-4">
                    <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
                        <FileText size={12}/> Sources
                    </div>
                    {sources.length > 0 ? (
                        sources.map((source, i) => (
                            <div key={i} className="text-xs text-indigo-300 truncate hover:text-indigo-200">
                                {source}
                            </div>
                        ))
                    ) : (
                        <div className="text-xs text-gray-500">No sources cited</div>
                    )}
                </div>

                <div className="absolute bottom-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity text-xs text-gray-500 flex items-center gap-1">
                    <RefreshCw size={12}/> {isFlipped ? "Close details" : "View analysis"}
                </div>
            </GlassCard>
        </div>
    );
};

// =============================================================================
// ROLE-BASED DECISION CARD
// =============================================================================

const RoleBasedDecisionCard = ({ report, registry }: { report: AnalysisReport; registry: Record<string, SourceMetadata> }) => {
    const insight = getRoleBasedInsight(report);
    const decisionStyle = getDecisionStyle(insight.decision);
    const citationComponents = createCitationComponents(registry);

    return (
        <GlassCard className={cn("border-l-4", decisionStyle.border)}>
            <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                <div className="flex items-start gap-4">
                    <div className={cn("w-14 h-14 rounded-xl flex items-center justify-center", decisionStyle.bg)}>
                        <decisionStyle.Icon size={28} className={decisionStyle.color} />
                    </div>
                    <div>
                        <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">
                                {getPersonaLabel(insight.user_role)} Recommendation
                            </span>
                        </div>
                        <h2 className={cn("text-3xl font-bold", decisionStyle.color)}>
                            {insight.decision}
                        </h2>
                        <div className="flex items-center gap-2 mt-2">
                            <div className={cn("px-2 py-1 rounded text-xs font-bold border", getScoreColor(insight.confidence_score))}>
                                {insight.confidence_score}% Confidence
                            </div>
                        </div>
                    </div>
                </div>

                {/* Key Concerns */}
                {insight.key_concerns && insight.key_concerns.length > 0 && (
                    <div className="flex-1 md:max-w-sm">
                        <div className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-1">
                            <AlertTriangle size={12} /> Key Concerns
                        </div>
                        <div className="space-y-1">
                            {insight.key_concerns.slice(0, 3).map((concern, idx) => (
                                <div key={idx} className="text-sm text-gray-300 flex items-start gap-2">
                                    <span className="text-red-400">•</span>
                                    <ReactMarkdown components={citationComponents}>
                                        {concern}
                                    </ReactMarkdown>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Justification */}
            <div className="mt-4 pt-4 border-t border-white/10">
                <div className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Justification</div>
                <div className="text-sm text-gray-300 prose prose-invert prose-sm max-w-none line-clamp-3">
                    <ReactMarkdown components={citationComponents}>
                        {insight.justification}
                    </ReactMarkdown>
                </div>
            </div>
        </GlassCard>
    );
};

// =============================================================================
// DEBATE REPORT SECTION
// =============================================================================

const DebateReportSection = ({ report, registry }: { report: AnalysisReport; registry: Record<string, SourceMetadata> }) => {
    const debateReport = getDebateReport(report);
    const citationComponents = createCitationComponents(registry);

    if (!debateReport) {
        // Fallback to legacy bull_case / bear_case
        return (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <GlassCard className="border-l-2 border-l-blue-500/50">
                    <div className="flex items-center gap-2 mb-4">
                        <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center">
                            <FileText size={16} className="text-blue-400" />
                        </div>
                        <h3 className="font-semibold text-white">Investment Summary</h3>
                    </div>
                    <div className="text-sm text-gray-300 prose prose-invert prose-sm max-w-none max-h-[250px] overflow-y-auto custom-scrollbar">
                        <ReactMarkdown components={citationComponents}>{report.summary}</ReactMarkdown>
                    </div>
                </GlassCard>

                <GlassCard className="border-l-2 border-l-emerald-500/50">
                    <div className="flex items-center gap-2 mb-4">
                        <div className="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                            <TrendingUp size={16} className="text-emerald-400" />
                        </div>
                        <h3 className="font-semibold text-white">Bull Case</h3>
                    </div>
                    <div className="text-sm text-gray-300 prose prose-invert prose-sm max-w-none max-h-[250px] overflow-y-auto custom-scrollbar">
                        <ReactMarkdown components={citationComponents}>{report.bull_case}</ReactMarkdown>
                    </div>
                </GlassCard>

                <GlassCard className="border-l-2 border-l-amber-500/50">
                    <div className="flex items-center gap-2 mb-4">
                        <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center">
                            <AlertTriangle size={16} className="text-amber-400" />
                        </div>
                        <h3 className="font-semibold text-white">Risks & Concerns</h3>
                    </div>
                    <div className="text-sm text-gray-300 prose prose-invert prose-sm max-w-none max-h-[250px] overflow-y-auto custom-scrollbar">
                        <ReactMarkdown components={citationComponents}>{report.risk_factors}</ReactMarkdown>
                    </div>
                </GlassCard>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center gap-2 mb-2">
                <Gavel size={20} className="text-purple-400" />
                <h3 className="text-lg font-bold text-white">Agent Debate</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Government (Pro) */}
                <GlassCard className="border-l-2 border-l-emerald-500/50">
                    <div className="flex items-center gap-2 mb-4">
                        <div className="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                            <TrendingUp size={16} className="text-emerald-400" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-white">Government (Pro)</h3>
                            <p className="text-xs text-gray-400">Bullish Arguments</p>
                        </div>
                    </div>
                    <div className="text-sm text-emerald-300 mb-3 italic">
                        "{debateReport.government_stand.stance_summary}"
                    </div>
                    <div className="space-y-2 max-h-[200px] overflow-y-auto custom-scrollbar">
                        {debateReport.government_stand.arguments.map((arg, idx) => (
                            <div key={idx} className="text-sm text-gray-300 flex items-start gap-2">
                                <span className="text-emerald-400 font-bold">{idx + 1}.</span>
                                <ReactMarkdown components={citationComponents}>
                                    {arg}
                                </ReactMarkdown>
                            </div>
                        ))}
                    </div>
                </GlassCard>

                {/* Opposition (Skeptic) */}
                <GlassCard className="border-l-2 border-l-red-500/50">
                    <div className="flex items-center gap-2 mb-4">
                        <div className="w-8 h-8 rounded-lg bg-red-500/20 flex items-center justify-center">
                            <TrendingDown size={16} className="text-red-400" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-white">Opposition (Skeptic)</h3>
                            <p className="text-xs text-gray-400">Bearish Arguments</p>
                        </div>
                    </div>
                    <div className="text-sm text-red-300 mb-3 italic">
                        "{debateReport.opposition_stand.stance_summary}"
                    </div>
                    <div className="space-y-2 max-h-[200px] overflow-y-auto custom-scrollbar">
                        {debateReport.opposition_stand.arguments.map((arg, idx) => (
                            <div key={idx} className="text-sm text-gray-300 flex items-start gap-2">
                                <span className="text-red-400 font-bold">{idx + 1}.</span>
                                <ReactMarkdown components={citationComponents}>
                                    {arg}
                                </ReactMarkdown>
                            </div>
                        ))}
                    </div>
                </GlassCard>
            </div>

            {/* Judge Verdict */}
            <GlassCard className="border-l-2 border-l-purple-500/50">
                <div className="flex items-center gap-2 mb-4">
                    <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center">
                        <Gavel size={16} className="text-purple-400" />
                    </div>
                    <h3 className="font-semibold text-white">Judge's Verdict</h3>
                </div>

                {/* Verdict Decision */}
                <div className="text-xl font-bold text-purple-400 mb-3">
                    {debateReport.judge_verdict}
                </div>

                {/* Verdict Reasoning (only if present) */}
                {debateReport.verdict_reasoning && (
                    <div className="mb-4">
                        <div className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Reasoning</div>
                        <div className="text-sm text-gray-300 prose prose-invert prose-sm max-w-none bg-white/5 p-3 rounded-lg border border-white/10">
                            <ReactMarkdown components={citationComponents}>{debateReport.verdict_reasoning}</ReactMarkdown>
                        </div>
                    </div>
                )}

                {/* Key Deciding Factors (only if present) */}
                {debateReport.verdict_key_factors && debateReport.verdict_key_factors.length > 0 && (
                    <div>
                        <div className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-1">
                            <Scale size={12} /> Key Deciding Factors
                        </div>
                        <div className="space-y-2">
                            {debateReport.verdict_key_factors.map((factor, idx) => (
                                <div key={idx} className="text-sm text-gray-300 flex items-start gap-2 bg-white/5 p-2 rounded-lg border border-white/5">
                                    <span className="text-purple-400 font-bold">{idx + 1}.</span>
                                    <div className="prose prose-invert prose-sm max-w-none">
                                        <ReactMarkdown components={citationComponents}>
                                            {factor}
                                        </ReactMarkdown>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </GlassCard>
        </div>
    );
};

// =============================================================================
// FINANCIAL ANALYSIS VIEW
// =============================================================================

export const FinancialAnalysisView = ({ report }: { report: AnalysisReport }) => {
    const [flippedCard, setFlippedCard] = useState<string | null>(null);
    const registry = getCitationRegistry(report);

    const financial = report.financial_analysis || {};

    // Map new structure with fallbacks
    const getSection = (key: string): SectionContent => {
        const section = (financial as any)[key];
        if (section && section.preview_summary) {
            return section;
        }
        // Fallback for empty/missing data
        return {
            preview_summary: "No data available",
            detailed_findings: [],
            confidence_score: 0,
            highlights: []
        };
    };

    const cards = [
        {
            id: 'valuation',
            title: "Valuation",
            data: getSection('valuation'),
            icon: BarChart3,
            borderColor: 'border-l-blue-500/50',
            bgColor: 'bg-blue-500/20',
            textColor: 'text-blue-400'
        },
        {
            id: 'profitability',
            title: "Profitability",
            data: getSection('profitability'),
            icon: TrendingUp,
            borderColor: 'border-l-amber-500/50',
            bgColor: 'bg-amber-500/20',
            textColor: 'text-amber-400'
        },
        {
            id: 'growth',
            title: "Growth",
            data: getSection('growth'),
            icon: TrendingUp,
            borderColor: 'border-l-emerald-500/50',
            bgColor: 'bg-emerald-500/20',
            textColor: 'text-emerald-400'
        },
        {
            id: 'financial_health',
            title: "Financial Health",
            data: getSection('financial_health'),
            icon: Shield,
            borderColor: 'border-l-indigo-500/50',
            bgColor: 'bg-indigo-500/20',
            textColor: 'text-indigo-400'
        },
    ];

    return (
        <div className={cn(
            "grid gap-4 transition-all duration-500",
            flippedCard ? "grid-cols-1" : "grid-cols-1 md:grid-cols-2"
        )}>
            {cards.map(card => {
                if (flippedCard && flippedCard !== card.id) return null;

                return (
                    <SectionCard
                        key={card.id}
                        id={card.id}
                        title={card.title}
                        data={card.data}
                        icon={card.icon}
                        borderColor={card.borderColor}
                        bgColor={card.bgColor}
                        textColor={card.textColor}
                        isFlipped={flippedCard === card.id}
                        onFlip={() => setFlippedCard(prev => prev === card.id ? null : card.id)}
                        registry={registry}
                    />
                );
            })}
        </div>
    );
};

// =============================================================================
// ESG ANALYSIS VIEW
// =============================================================================

const ESGAnalysisView = ({ report }: { report: AnalysisReport }) => {
    const [flippedCard, setFlippedCard] = useState<string | null>(null);
    const registry = getCitationRegistry(report);

    const esg = report.esg_analysis || {};

    // Map new structure with fallbacks
    const getSection = (key: string): SectionContent => {
        const section = (esg as any)[key];
        if (section && section.preview_summary) {
            return section;
        }
        return {
            preview_summary: "No data available",
            detailed_findings: [],
            confidence_score: 0,
            highlights: []
        };
    };

    const overviewData = getSection('overview');

    const cards = [
        {
            id: 'governance',
            title: "Governance & ESG Integration",
            data: getSection('governance_integration'),
            icon: Building2,
            borderColor: 'border-l-amber-500/50',
            bgColor: 'bg-amber-500/20',
            textColor: 'text-amber-400'
        },
        {
            id: 'environmental',
            title: "Environmental",
            data: getSection('environmental'),
            icon: Leaf,
            borderColor: 'border-l-emerald-500/50',
            bgColor: 'bg-emerald-500/20',
            textColor: 'text-emerald-400'
        },
        {
            id: 'social',
            title: "Social",
            data: getSection('social'),
            icon: Users,
            borderColor: 'border-l-blue-500/50',
            bgColor: 'bg-blue-500/20',
            textColor: 'text-blue-400'
        },
        {
            id: 'disclosure',
            title: "Disclosure Quality",
            data: getSection('disclosure_quality'),
            icon: Eye,
            borderColor: 'border-l-indigo-500/50',
            bgColor: 'bg-indigo-500/20',
            textColor: 'text-indigo-400'
        },
    ];

    return (
        <div className="space-y-4">
            {/* Overview Card - Full Width */}
            {(!flippedCard || flippedCard === 'overview') && (
                <SectionCard
                    id="overview"
                    title="Overview"
                    data={overviewData}
                    icon={Leaf}
                    borderColor="border-l-emerald-500/50"
                    bgColor="bg-emerald-500/20"
                    textColor="text-emerald-400"
                    isFlipped={flippedCard === 'overview'}
                    onFlip={() => setFlippedCard(prev => prev === 'overview' ? null : 'overview')}
                    registry={registry}
                    isMain
                />
            )}

            {/* Other 4 Cards - 2x2 Grid */}
            <div className={cn(
                "grid gap-4 transition-all duration-500",
                flippedCard && flippedCard !== 'overview' ? "grid-cols-1" : "grid-cols-1 md:grid-cols-2"
            )}>
                {cards.map(card => {
                    if (flippedCard && flippedCard !== card.id) return null;

                    return (
                        <SectionCard
                            key={card.id}
                            id={card.id}
                            title={card.title}
                            data={card.data}
                            icon={card.icon}
                            borderColor={card.borderColor}
                            bgColor={card.bgColor}
                            textColor={card.textColor}
                            isFlipped={flippedCard === card.id}
                            onFlip={() => setFlippedCard(prev => prev === card.id ? null : card.id)}
                            registry={registry}
                        />
                    );
                })}
            </div>
        </div>
    );
};

// =============================================================================
// ROLE ANALYSIS VIEW
// =============================================================================

const RoleAnalysisView = ({ report }: { report: AnalysisReport }) => {
    const registry = getCitationRegistry(report);
    const insight = getRoleBasedInsight(report);
    const citationComponents = createCitationComponents(registry);

    return (
        <div className="space-y-6">
            <GlassCard className="border-l-4 border-l-purple-500/50">
                <div className="flex items-center gap-2 mb-4">
                    <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center">
                        <Users size={16} className="text-purple-400" />
                    </div>
                    <h3 className="font-semibold text-white text-lg">Detailed Role Analysis: {getPersonaLabel(insight.user_role)}</h3>
                </div>

                <div className="space-y-6">
                     {/* Justification */}
                    <div>
                        <div className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Detailed Justification</div>
                        <div className="text-sm text-gray-300 prose prose-invert prose-sm max-w-none">
                            <ReactMarkdown components={citationComponents}>
                                {insight.justification || "No specific justification provided."}
                            </ReactMarkdown>
                        </div>
                    </div>

                    {/* Key Concerns */}
                    <div>
                        <div className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-1">
                            <AlertTriangle size={12} /> Key Concerns
                        </div>
                        {insight.key_concerns && insight.key_concerns.length > 0 ? (
                            <div className="space-y-3">
                                {insight.key_concerns.map((concern, idx) => (
                                    <div key={idx} className="text-sm text-gray-300 flex items-start gap-2 bg-white/5 p-3 rounded-lg border border-white/5">
                                        <span className="text-red-400 mt-1">•</span>
                                        <div className="prose prose-invert prose-sm max-w-none">
                                            <ReactMarkdown components={citationComponents}>
                                                {concern}
                                            </ReactMarkdown>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                             <div className="text-sm text-gray-400 italic bg-white/5 p-3 rounded-lg border border-white/5">
                                No major concerns identified based on available data.
                            </div>
                        )}
                    </div>
                </div>
            </GlassCard>
        </div>
    );
};

// =============================================================================
// MARKET SENTIMENT VIEW
// =============================================================================

const MarketSentimentCard = ({ report, registry }: { report: AnalysisReport; registry: Record<string, SourceMetadata> }) => {
    const sentiment = getMarketSentiment(report);
    const citationComponents = createCitationComponents(registry);

    if (!sentiment) {
        return (
            <GlassCard className="border-l-4 border-l-gray-500/50">
                <div className="text-gray-400 text-center py-8">
                    <p>No market sentiment data available.</p>
                </div>
            </GlassCard>
        );
    }

    const getSentimentColor = (sent: string) => {
        switch (sent?.toUpperCase()) {
            case 'POSITIVE': return 'text-emerald-400 bg-emerald-500/20 border-emerald-500/50';
            case 'NEGATIVE': return 'text-red-400 bg-red-500/20 border-red-500/50';
            default: return 'text-gray-400 bg-gray-500/20 border-gray-500/50';
        }
    };

    const sentimentStyle = getSentimentColor(sentiment.sentiment);

    return (
        <div className="space-y-6">
            <GlassCard className={cn("border-l-4", sentimentStyle.split(' ').pop())}>
                <div className="flex items-center gap-4 mb-6">
                    <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center", sentimentStyle.split(' ')[1])}>
                        <TrendingUp size={24} className={sentimentStyle.split(' ')[0]} />
                    </div>
                    <div>
                        <div className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">Market Sentiment</div>
                        <h2 className={cn("text-2xl font-bold", sentimentStyle.split(' ')[0])}>
                            {sentiment.sentiment}
                        </h2>
                    </div>
                </div>

                <div className="space-y-6">
                    {/* Summary */}
                    <div>
                        <div className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Summary</div>
                        <div className="text-sm text-gray-300 prose prose-invert prose-sm max-w-none">
                            <ReactMarkdown components={citationComponents}>
                                {sentiment.summary}
                            </ReactMarkdown>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Key Events */}
                        <div>
                            <div className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-1">
                                <MessageSquare size={12} /> Key Events
                            </div>
                            {sentiment.key_events && sentiment.key_events.length > 0 ? (
                                <div className="space-y-2">
                                    {sentiment.key_events.map((event, idx) => (
                                        <div key={idx} className="text-sm text-gray-300 flex items-start gap-2 bg-white/5 p-2 rounded-lg border border-white/5">
                                            <span className="text-blue-400 mt-0.5">•</span>
                                            <div className="prose prose-invert prose-sm max-w-none">
                                                <ReactMarkdown components={citationComponents}>
                                                    {event}
                                                </ReactMarkdown>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-sm text-gray-500 italic">No key events found.</div>
                            )}
                        </div>

                        {/* Risks from News */}
                        <div>
                            <div className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-1">
                                <AlertTriangle size={12} /> News-Based Risks
                            </div>
                            {sentiment.risks_from_news && sentiment.risks_from_news.length > 0 ? (
                                <div className="space-y-2">
                                    {sentiment.risks_from_news.map((risk, idx) => (
                                        <div key={idx} className="text-sm text-gray-300 flex items-start gap-2 bg-white/5 p-2 rounded-lg border border-white/5">
                                            <span className="text-red-400 mt-0.5">•</span>
                                            <div className="prose prose-invert prose-sm max-w-none">
                                                <ReactMarkdown components={citationComponents}>
                                                    {risk}
                                                </ReactMarkdown>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-sm text-gray-500 italic">No significant risks found in news.</div>
                            )}
                        </div>
                    </div>
                </div>
            </GlassCard>
        </div>
    );
};

// =============================================================================
// MAIN ANALYSIS RESULTS VIEW
// =============================================================================

export const AnalysisResultsView = ({ report, onReanalyze, onDelete }: { report: AnalysisReport, onReanalyze: () => void, onDelete?: () => void }) => {
    const [showDetails, setShowDetails] = useState(false);
    const [viewMode, setViewMode] = useState<'esg' | 'financial' | 'debate' | 'role' | 'sentiment'>('role');

    const registry = getCitationRegistry(report);

    return (
        <div className="space-y-6 mt-6">
            {/* Role-Based Decision Card */}
            <RoleBasedDecisionCard report={report} registry={registry} />

            {/* Main Analysis Card */}
            <GlassCard className="space-y-6">
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
                                onClick={() => setViewMode('role')}
                                className={cn(
                                    "px-3 py-1.5 rounded-md text-sm font-medium transition-all",
                                    viewMode === 'role' ? "bg-purple-500 text-white shadow-lg" : "text-gray-400 hover:text-white"
                                )}
                            >
                                Role View
                            </button>
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
                            <button
                                onClick={() => setViewMode('debate')}
                                className={cn(
                                    "px-3 py-1.5 rounded-md text-sm font-medium transition-all",
                                    viewMode === 'debate' ? "bg-purple-500 text-white shadow-lg" : "text-gray-400 hover:text-white"
                                )}
                            >
                                Debate
                            </button>
                            <button
                                onClick={() => setViewMode('sentiment')}
                                className={cn(
                                    "px-3 py-1.5 rounded-md text-sm font-medium transition-all",
                                    viewMode === 'sentiment' ? "bg-blue-500 text-white shadow-lg" : "text-gray-400 hover:text-white"
                                )}
                            >
                                Sentiment
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
                    </div>
                </div>

                {/* Legend */}
                <div className="flex items-center justify-center gap-6 text-xs text-gray-500 pt-2 pb-4">
                    <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-emerald-500"/> High Confidence (80%+)</div>
                    <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-amber-500"/> Medium Confidence (60-79%)</div>
                    <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-red-500"/> Low Confidence (&lt;60%)</div>
                </div>

                {/* Content based on view mode */}
                {viewMode === 'role' && <RoleAnalysisView report={report} />}
                {viewMode === 'esg' && <ESGAnalysisView report={report} />}
                {viewMode === 'financial' && <FinancialAnalysisView report={report} />}
                {viewMode === 'debate' && <DebateReportSection report={report} registry={registry} />}
                {viewMode === 'sentiment' && <MarketSentimentCard report={report} registry={registry} />}

                {/* Citation Registry Info */}
                <div className="text-center text-xs text-gray-600 mt-8 flex items-center justify-center gap-2">
                    <Info size={12} />
                    <span>Click on citations [N#], [F#], [D#] to view source details</span>
                    <span className="text-gray-700">|</span>
                    <span>{Object.keys(registry).length} sources cited</span>
                </div>
            </GlassCard>
        </div>
    );
};

// =============================================================================
// MAIN WIZARD COMPONENT
// =============================================================================

export function AnalysisWizardModal({ isOpen, onClose, onComplete, companyName, companyId }: AnalysisWizardModalProps) {
    const [step, setStep] = useState<AnalysisStep>('topic');
    const [topic, setTopic] = useState<AnalysisTopic | null>(null);

    useEffect(() => {
        if (!isOpen) {
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
            case 'progress': return "";
            case 'results': return "";
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
                            companyName={companyName}
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
            </AnimatePresence>
        </GlassModal>
    );
}

export default AnalysisWizardModal;
