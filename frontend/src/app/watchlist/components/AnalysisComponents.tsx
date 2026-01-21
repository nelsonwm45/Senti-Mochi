'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
    Check, Upload, FileText, Leaf, BarChart3, 
    Building2, Loader2, ChevronRight, X, ArrowLeft,
    RefreshCw, Info, ExternalLink
} from 'lucide-react';
import { GlassModal, GlassModalFooter } from '@/components/ui/GlassModal';
import { GlassButton } from '@/components/ui/GlassButton';
import { GlassCard } from '@/components/ui/GlassCard';
import { cn } from '@/lib/utils';

// --- Types ---

type AnalysisStep = 'topic' | 'upload' | 'progress' | 'results';
type AnalysisTopic = 'esg' | 'financials' | 'general';
type AnalysisStatus = 'waiting' | 'loading' | 'completed';

interface AnalysisWizardModalProps {
    isOpen: boolean;
    onClose: () => void;
    onComplete: () => void; // New prop for signaling completion
    companyName: string;
}

// --- Mock Data ---

const ESG_RESULTS = {
    overview: {
        score: 85,
        summary: "The company demonstrates a strong commitment to sustainability with comprehensive ESG policies in place. Recent initiatives show significant progress in reducing carbon footprint and improving stakeholder engagement.",
        citations: ["[1]", "[2]", "[3]"],
        sources: [
            "2023 Sustainability Report - p. 4-7",
            "CDP Climate Disclosure 2023"
        ]
    },
    governance: {
        score: 78,
        summary: "Board-level ESG oversight with dedicated sustainability committee. Executive compensation tied to ESG metrics. Clear governance framework with regular third-party audits and transparent reporting practices.",
        citations: ["[1]", "[2]"],
        sources: [
            "Corporate Governance Report 2023 - p. 12"
        ]
    },
    environmental: {
        score: 82,
        summary: "Strong environmental performance with science-based targets. Water usage reduced by 25%. Waste diversion rate at 85%. Biodiversity protection programs implemented across major operational sites.",
        citations: ["[1]", "[2]", "[3]"],
        sources: [
            "CDP Water Security 2023"
        ]
    },
    social: {
        score: 76,
        summary: "Employee satisfaction scores above industry average. Robust DEI initiatives with measurable progress. Community investment programs reaching over 50,000 beneficiaries annually. Strong supply chain labor standards.",
        citations: ["[1]", "[2]"],
        sources: [
            "DEI Report 2023 - p. 8-15"
        ]
    },
    disclosure: {
        score: 88,
        summary: "Comprehensive reporting aligned with GRI, SASB, and TCFD frameworks. Data assurance by Big Four auditor. Clear targets with measurable KPIs. Strong stakeholder communication and engagement practices.",
        citations: ["[1]", "[2]", "[3]"],
        sources: [
            "GRI Content Index 2023"
        ]
    }
};

const DETAILED_ANALYSIS = {
    claims: "The company has made extensive public commitments across ESG dimensions. Key claims include carbon neutrality targets, diversity initiatives, and governance reforms. Our analysis cross-references these claims against verifiable data sources.",
    sources: "Analysis incorporates data from 47 news sources, 12 analyst reports, and 8 third-party rating agencies. Recent coverage has been largely positive with focus on environmental initiatives. Some concerns raised about social metrics verification.",
    judge: "Overall confidence score of 82% reflects strong documentation and third-party verification. Key strength: transparent environmental reporting. Areas for improvement: more granular social impact metrics and enhanced Scope 3 reporting. Recommendation: maintain current trajectory."
};

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
const FileUploadStep = ({ onNext, onBack, onCancel }: { onNext: () => void, onBack: () => void, onCancel: () => void }) => {
    const [isDragging, setIsDragging] = useState(false);
    const [files, setFiles] = useState<File[]>([]);

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        // Mock file acceptance
        if (e.dataTransfer.files?.length) {
             setFiles(prev => [...prev, ...Array.from(e.dataTransfer.files)]);
        }
    };

    return (
        <div className="space-y-6">
            <div 
                className={cn(
                    "border-2 border-dashed rounded-2xl h-64 flex flex-col items-center justify-center transition-all",
                    isDragging ? "border-accent bg-accent/5 scale-[1.02]" : "border-white/10 hover:border-white/20 bg-white/[0.02]"
                )}
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleDrop}
            >
                <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4 text-gray-400">
                    <Upload size={32} />
                </div>
                <h3 className="text-lg font-medium text-white mb-2">Drag & drop PDF files here</h3>
                <p className="text-sm text-gray-500">or click to browse</p>
                {files.length > 0 && (
                     <div className="mt-4 text-sm text-emerald-400 font-medium">
                         {files.length} file{files.length > 1 ? 's' : ''} selected
                     </div>
                )}
            </div>

            <GlassModalFooter className="justify-between">
                <GlassButton variant="ghost" onClick={onBack} leftIcon={<ArrowLeft size={16}/>}>Back</GlassButton>
                <div className="flex gap-2">
                    <GlassButton variant="ghost" onClick={onCancel}>Cancel</GlassButton>
                    <GlassButton 
                        onClick={onNext} 
                        // Allow proceeding without files for demo purposes if desired, but request implies upload
                        // For now we'll allow it ("simulate")
                    >
                        Confirm ({files.length} files)
                    </GlassButton>
                </div>
            </GlassModalFooter>
        </div>
    );
};

// 3. Progress
const ProgressStep = ({ onComplete }: { onComplete: () => void }) => {
    const [stepIndex, setStepIndex] = useState(0);
    const steps = [
        { label: "PDF Upload", sub: "Uploading your documents" },
        { label: "Pulling News", sub: "Gathering recent news articles" },
        { label: "Extracting Data", sub: "Processing document content" },
        { label: "Verifying Claims", sub: "Cross-referencing sources" },
        { label: "Generating Insights", sub: "Creating analysis report" }
    ];

    useEffect(() => {
        const interval = setInterval(() => {
            setStepIndex(prev => {
                if (prev >= steps.length - 1) {
                    clearInterval(interval);
                    setTimeout(onComplete, 800);
                    return prev;
                }
                return prev + 1;
            });
        }, 1200); // 1.2s per step
        return () => clearInterval(interval);
    }, [onComplete]);

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
export const AnalysisResultsView = ({ onReanalyze }: { onReanalyze: () => void }) => {
    // Card State Management
    const [flippedCard, setFlippedCard] = useState<string | null>(null);
    const [showDetails, setShowDetails] = useState(false); // Toggle for top 3 cards

    const toggleFlip = (cardId: string) => {
        setFlippedCard(prev => prev === cardId ? null : cardId);
    };

    const cards = [
        { id: 'overview', title: "Overview", data: ESG_RESULTS.overview, color: "text-emerald-400" },
        { id: 'governance', title: "Governance & ESG Integration", data: ESG_RESULTS.governance, color: "text-amber-400" },
        { id: 'environmental', title: "Environmental", data: ESG_RESULTS.environmental, color: "text-emerald-400" },
        { id: 'social', title: "Social", data: ESG_RESULTS.social, color: "text-amber-400" },
        { id: 'disclosure', title: "Disclosure Quality & Maturity", data: ESG_RESULTS.disclosure, color: "text-emerald-400" },
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
                        <span className="text-lg font-bold text-emerald-400">82%</span>
                    </div>
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
                             <GlassCard className="space-y-4">
                                 <h3 className="font-semibold text-white">Company Claims</h3>
                                 <p className="text-sm text-gray-400 leading-relaxed">{DETAILED_ANALYSIS.claims}</p>
                             </GlassCard>
                             <GlassCard className="space-y-4">
                                 <h3 className="font-semibold text-white">News & Third-Party Sources</h3>
                                 <p className="text-sm text-gray-400 leading-relaxed">{DETAILED_ANALYSIS.sources}</p>
                             </GlassCard>
                             <GlassCard className="space-y-4">
                                 <h3 className="font-semibold text-white">Judge's Analysis & Confidence</h3>
                                 <p className="text-sm text-gray-400 leading-relaxed">{DETAILED_ANALYSIS.judge}</p>
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

            {/* Overview Card - Full Width */}
            {(() => {
                const overviewCard = cards.find(c => c.id === 'overview')!;
                const isFlipped = flippedCard === overviewCard.id;
                return (
                    <div 
                        className={cn(
                            "relative perspective-1000 transition-all duration-500",
                            isFlipped ? "h-[400px]" : "h-[200px]"
                        )}
                    >
                        <GlassCard 
                            className="h-full cursor-pointer hover:border-white/20 transition-all group overflow-hidden flex flex-col"
                            onClick={() => toggleFlip(overviewCard.id)}
                        >
                            <div className="flex justify-between items-start mb-4">
                                 <div className="flex items-center gap-2">
                                    <span className="text-[10px] font-bold uppercase tracking-wider bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded">Main</span>
                                    <h3 className="font-bold text-white text-lg">{overviewCard.title}</h3>
                                 </div>
                                 <div className={cn("px-2 py-1 rounded-lg text-xs font-bold border", getScoreColor(overviewCard.data.score))}>
                                     {overviewCard.data.score}%
                                 </div>
                            </div>
                            
                            <p className="text-sm text-gray-400 leading-relaxed mb-6 flex-1">
                                {overviewCard.data.summary}
                                 <span className="text-emerald-500/70 text-xs ml-1 font-mono tracking-tighter align-super">
                                     {overviewCard.data.citations.join('')}
                                 </span>
                            </p>
                            
                            <div className="mt-auto border-t border-white/5 pt-4">
                                <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
                                    <FileText size={12}/> Sources
                                </div>
                                <div className="flex flex-wrap gap-4">
                                    {overviewCard.data.sources.map((source, i) => (
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

                     return (
                         <div 
                            key={card.id} 
                            className={cn(
                                "relative perspective-1000 transition-all duration-500",
                                isFlipped ? "md:col-span-2 h-[400px]" : "h-[220px]"
                            )}
                         >
                            <GlassCard 
                                className="h-full cursor-pointer hover:border-white/20 transition-all group overflow-hidden flex flex-col"
                                onClick={() => toggleFlip(card.id)}
                            >
                                <div className="flex justify-between items-start mb-4">
                                     <div className="flex items-center gap-2">
                                        <h3 className="font-bold text-white text-lg">{card.title}</h3>
                                     </div>
                                     <div className={cn("px-2 py-1 rounded-lg text-xs font-bold border", getScoreColor(card.data.score))}>
                                         {card.data.score}%
                                     </div>
                                </div>
                                
                                <p className="text-sm text-gray-400 leading-relaxed mb-6 flex-1">
                                    {card.data.summary}
                                     <span className="text-emerald-500/70 text-xs ml-1 font-mono tracking-tighter align-super">
                                         {card.data.citations.join('')}
                                     </span>
                                </p>
                                
                                <div className="mt-auto border-t border-white/5 pt-4">
                                    <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
                                        <FileText size={12}/> Sources
                                    </div>
                                    {card.data.sources.map((source, i) => (
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
            
            <div className="text-center text-xs text-gray-600 mt-8">
                Click on any card to flip and see the detailed analysis backing
            </div>
        </GlassCard>
    );
};


// --- Main Wizard Component ---

export function AnalysisWizardModal({ isOpen, onClose, onComplete, companyName }: AnalysisWizardModalProps) {
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
