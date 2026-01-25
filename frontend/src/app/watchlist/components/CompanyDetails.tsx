'use client';

import { useState, useEffect } from 'react';
import { ArrowLeft, FileText, Upload, PieChart, BarChart3, TrendingUp, TrendingDown, Minus, Loader2, FileDown, Clock, ExternalLink, ChevronRight, Trash2, BrainCircuit, Info, AlertTriangle } from 'lucide-react';
import { GlassCard } from '@/components/ui/GlassCard';
import { formatDistanceToNow, format } from 'date-fns';
import { getKeyMetrics, formatValue, formatPercent } from '../utils';
import CompanyDocumentUpload from '@/components/documents/CompanyDocumentUpload';
import { AnalysisWizardModal, AnalysisResultsView } from './AnalysisComponents';
import { GlassButton } from '@/components/ui/GlassButton';
import { Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';
import { AnalysisReport, analysisApi } from '@/lib/api/analysis';

interface CompanyDetailsProps {
    ticker: string;
    onBack: () => void;
}

const tabs = [
    { id: 'details', label: 'Details', icon: FileText },
    { id: 'analysis', label: 'Company Analysis', icon: Sparkles },
    { id: 'uploads', label: 'Uploads', icon: Upload },
    { id: 'annual-reports', label: 'Annual Reports', icon: FileDown },
    { id: 'is', label: 'Income Statement', icon: BarChart3 },
    { id: 'bs', label: 'Balance Sheet', icon: PieChart },
    { id: 'cf', label: 'Cash Flow', icon: TrendingUp },
];

interface AnnualReport {
    id: string;
    title: string;
    date: string;
    link: string;
}

// Helper: Decode HTML entities
const decodeHtml = (html: string): string => {
    const txt = document.createElement('textarea');
    txt.innerHTML = html;
    return txt.value;
};

// Helper: Parse HTML link
const parseHtmlLink = (htmlString: string): { text: string; link?: string } => {
    const decoded = decodeHtml(htmlString);
    const linkMatch = decoded.match(/<a[^>]+href=['"]([^'"]+)['"][^>]*>(.*?)<\/a>/i);
    if (linkMatch) {
        return {
            text: linkMatch[2].replace(/<[^>]*>/g, '').trim(),
            link: linkMatch[1]
        };
    }
    const text = decoded.replace(/<[^>]*>/g, '').trim();
    return { text };
};



// Recommended order for financial statements
const IS_ORDER = [
    'Total Revenue', 'Revenue', 'Cost Of Revenue', 'Gross Profit',
    'Operating Expense', 'Operating Income', 'Net Non Operating Interest Income Expense',
    'Pretax Income', 'Tax Provision', 'Net Income Common Stockholders',
    'Net Income', 'Diluted NI Available to Com Stockholders', 'Basic EPS', 'Diluted EPS',
    'EBITDA', 'EBIT'
];

const BS_ORDER = [
    'Total Assets', 'Current Assets', 'Cash And Cash Equivalents',
    'Total Liabilities Net Minority Interest', 'Total Liabilities', 'Current Liabilities', 'Total Debt', 'Net Debt',
    'Total Equity Gross Minority Interest', 'Stockholders Equity',
    'Working Capital', 'Invested Capital'
];

const CF_ORDER = [
    'Operating Cash Flow', 'Investing Cash Flow', 'Financing Cash Flow',
    'Capital Expenditure', 'Free Cash Flow', 'End Cash Position',
    'Issuance Of Debt', 'Repayment Of Debt', 'Cash Dividends Paid'
];

const sortFinancialKeys = (keys: string[], orderList: string[]) => {
    return keys.sort((a, b) => {
        const idxA = orderList.indexOf(a);
        const idxB = orderList.indexOf(b);
        // If both in list, sort by index
        if (idxA !== -1 && idxB !== -1) return idxA - idxB;
        // If only A in list, A comes first
        if (idxA !== -1) return -1;
        // If only B in list, B comes first
        if (idxB !== -1) return 1;
        // If neither, sort alphabetically
        return a.localeCompare(b);
    });
};

const RatingBadge = ({ rating }: { rating: string }) => {
    const r = rating.toUpperCase();
    let color = "bg-gray-500/20 text-gray-400 border-gray-500/30";
    let icon = <Minus size={16} />;
    let text = "Neutral outlook. No clear signal.";

    if (r === 'BUY') {
        color = "bg-emerald-500/20 text-emerald-400 border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.3)]";
        icon = <TrendingUp size={16} />;
        text = "Strong potential for growth. Underlying fundamentals and sentiment exceed market expectations.";
    } else if (r === 'SELL') {
        color = "bg-rose-500/20 text-rose-400 border-rose-500/30 shadow-[0_0_15px_rgba(244,63,94,0.3)]";
        icon = <TrendingDown size={16} />; // Need direct import or use generic
        text = "Overvalued or facing significant headwinds. Risk factors outweigh potential returns.";
    } else if (r === 'HOLD') {
        color = "bg-amber-500/20 text-amber-400 border-amber-500/30 shadow-[0_0_15px_rgba(245,158,11,0.2)]";
        icon = <Minus size={16} />;
        text = "Fairly valued. Stability expected, but limited near-term upside catalyst.";
    }

    return (
        <div className="group relative flex items-center gap-2">
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border ${color} font-bold text-sm transition-all hover:scale-105`}>
                {icon}
                {r} RATING
                <Info size={14} className="opacity-70 ml-1" />
            </div>
            
            {/* Tooltip */}
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 bg-gray-900/95 backdrop-blur-md border border-white/10 rounded-xl text-xs text-gray-300 shadow-xl opacity-0 translate-y-2 pointer-events-none group-hover:opacity-100 group-hover:translate-y-0 group-hover:pointer-events-auto transition-all z-50">
                <div className="font-semibold text-white mb-1 border-b border-white/10 pb-1">{r} Logic</div>
                {text}
                <div className="absolute bottom-[-5px] left-1/2 -translate-x-1/2 w-3 h-3 bg-gray-900 border-r border-b border-white/10 rotate-45 transform"></div>
            </div>
        </div>
    );
};

export function CompanyDetails({ ticker, onBack }: CompanyDetailsProps) {
    const [company, setCompany] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('details');
    const [annualReports, setAnnualReports] = useState<AnnualReport[]>([]);
    const [analysisReports, setAnalysisReports] = useState<AnalysisReport[]>([]); // New State
    const [loadingReports, setLoadingReports] = useState(false);
    const [isAnalyzeModalOpen, setIsAnalyzeModalOpen] = useState(false);
    // showAnalysisResults is now derived from whether we have reports, or if we just finished one

    useEffect(() => {
        const fetchCompany = async () => {
            try {
                const res = await fetch(`/api/v1/companies/${ticker}`);
                if (!res.ok) throw new Error('Failed to fetch');
                const json = await res.json();
                setCompany(json);
                // Clear old reports when company changes
                setAnnualReports([]);
                setAnalysisReports([]);
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        };
        fetchCompany();
    }, [ticker]);

    // Fetch annual reports AND analysis reports when needed
    useEffect(() => {
        if (!company) return;

        if (activeTab === 'annual-reports') {
            fetchAnnualReports();
        } else if (activeTab === 'analysis') {
            fetchAnalysisReports();
        }
    }, [activeTab, company]);

    const fetchAnalysisReports = async () => {
        if (!company) return;
        try {
            const reports = await analysisApi.getReports(company.id);
            setAnalysisReports(reports);
        } catch (e) {
            console.error("Failed to fetch analysis reports", e);
        }
    };

    const fetchAnnualReports = async () => {
        if (!company) return;

        setLoadingReports(true);
        const reports: AnnualReport[] = [];
        const bursaCode = company.ticker.split('.')[0];

        // Log for debugging
        console.log(`[ANNUAL REPORTS] Fetching for ${company.name} (${company.ticker}) - Bursa Code: ${bursaCode}`);

        const url = `https://www.bursamalaysia.com/api/v1/announcements/search?ann_type=company&company=${bursaCode}&cat=AR,ARCO&per_page=20&page=0`;

        try {
            const response = await fetch(url, {
                method: 'GET',
                headers: { 'Accept': 'application/json' },
            });

            if (response.ok) {
                const data = await response.json();
                console.log(`[ANNUAL REPORTS] API returned ${data.data?.length || 0} items for ${bursaCode}`);

                if (data.data) {
                    for (const item of data.data) {
                        const dateMatch = parseHtmlLink(item[1]);
                        const titleMatch = parseHtmlLink(item[3]);
                        const link = titleMatch.link ? `https://www.bursamalaysia.com${titleMatch.link}` : '';
                        const idMatch = link.match(/ann_id=(\d+)/);
                        const reportId = idMatch ? `ar-${bursaCode}-${idMatch[1]}` : `ar-${bursaCode}-${item[0]}`;

                        // Verify the report is for this company by checking if the Bursa code appears in the title
                        // or if it's from the company-specific API call (which it should be)
                        reports.push({
                            id: reportId,
                            title: titleMatch.text,
                            date: dateMatch.text,
                            link: link
                        });
                    }
                }
            }
        } catch (err) {
            console.warn(`Error fetching annual reports for ${company.name}:`, err);
        }

        // API already returns data in reverse chronological order (newest first)
        console.log(`[ANNUAL REPORTS] Processed ${reports.length} reports for ${company.name}`);
        setAnnualReports(reports);
        setLoadingReports(false);
    };

    const handleAnalysisComplete = () => {
        // Refresh list after new analysis
        fetchAnalysisReports();
        // Force view to results if not already (logic handled by existence of report)
    };

    const handleDeleteReport = async (reportId: string, e: React.MouseEvent) => {
        e.stopPropagation(); // Prevent card click
        if (!confirm('Are you sure you want to delete this analysis report?')) return;

        try {
            await analysisApi.deleteReport(reportId);
            fetchAnalysisReports(); // Refresh the list
        } catch (error) {
            console.error('Failed to delete report:', error);
        }
    };

    // Derived state for latest report
    const latestAnalysisReport = analysisReports.length > 0 ? analysisReports[0] : null;

    if (loading) return <div className="flex justify-center p-12"><Loader2 className="animate-spin text-white" size={32} /></div>;
    if (!company) return <div>Company not found</div>;

    // Helper to get latest values for metrics
    const getMetrics = (category: string) => {
        const cat = company[category];
        if (!cat) return { metrics: {}, date: 'N/A' };
        const dates = Object.keys(cat).sort().reverse();
        const latestDate = dates[0];
        if (!latestDate) return { metrics: {}, date: 'N/A' };

        const metrics = cat[latestDate] as Record<string, number>;
        return { metrics, date: latestDate };
    };

    const { metrics: incomeStatement, date: isDate } = getMetrics('income_statement');
    const { metrics: balanceSheet, date: bsDate } = getMetrics('balance_sheet');
    const { metrics: cashFlow, date: cfDate } = getMetrics('cash_flow');
    const latestReportDate = isDate;

    const renderFinancialSection = (title: string, data: Record<string, number>, order: string[], date: string) => {
        const sortedKeys = sortFinancialKeys(Object.keys(data), order);

        return (
            <div className="bg-white/5 p-4 rounded-xl border border-white/10">
                <div className="flex justify-between items-center mb-4">
                    <div className="flex items-baseline gap-3">
                        <h3 className="text-lg font-semibold text-white">{title}</h3>
                        <span className="text-sm text-gray-400 font-mono">{date !== 'N/A' ? `Last updated: ${date}` : ''}</span>
                    </div>
                    <span className="text-xs text-gray-500">All numbers in base currency</span>
                </div>
                <div className="space-y-1">
                    {sortedKeys.map((key) => {
                        const value = data[key];
                        const isPositive = value >= 0;
                        const colorClass = isPositive ? 'text-green-400' : 'text-red-400';
                        return (
                            <div key={key} className="flex justify-between items-center py-2 border-b border-white/5 last:border-0 hover:bg-white/5 px-2 rounded group">
                                <span className="text-gray-400 text-sm group-hover:text-gray-300 transition-colors">{key}</span>
                                <span className={`font-mono text-sm ${colorClass}`}>{formatValue(value)}</span>
                            </div>
                        );
                    })}
                </div>
            </div>
        );
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center gap-4">
                <button
                    onClick={onBack}
                    className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors text-gray-300 hover:text-white"
                >
                    <ArrowLeft size={20} />
                </button>
                <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold text-xl shadow-lg bg-gradient-to-br from-indigo-500 to-purple-600`}>
                        {company.ticker[0]}
                    </div>
                    <div>
                        <div className="flex items-baseline gap-3">
                            <h1 className="text-2xl font-bold text-white leading-tight">{company.name}</h1>
                            <span className="text-sm text-gray-400 font-mono">{latestReportDate !== 'N/A' ? `Last updated: ${latestReportDate}` : ''}</span>
                        </div>
                        <div className="flex gap-2 text-sm text-gray-400">
                            <span>{company.ticker}</span>
                            <span>•</span>
                            <span>{company.sector}</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-1 overflow-x-auto pb-2 border-b border-white/10">
                {tabs.map((tab) => {
                    const Icon = tab.icon;
                    const isActive = activeTab === tab.id;
                    return (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`flex items-center gap-2 px-4 py-2.5 rounded-t-lg transition-all border-b-2 whitespace-nowrap ${isActive
                                    ? 'border-accent text-accent bg-white/5'
                                    : 'border-transparent text-gray-400 hover:text-white hover:bg-white/5'
                                }`}
                        >
                            <Icon size={16} />
                            <span className="font-medium">{tab.label}</span>
                        </button>
                    )
                })}
            </div>

            {/* Content */}
            <div className="min-h-[400px]">
                {activeTab === 'details' && (
                    <GlassCard className="space-y-4">
                        <h3 className="text-lg font-semibold text-white">About {company.name}</h3>
                        <p className="text-gray-300 leading-relaxed">
                            {company.name} is a company in the {company.sector} sector ({company.sub_sector}).
                            {company.website_url && <a href={company.website_url} target="_blank" rel="noopener noreferrer" className="block mt-2 text-indigo-400 hover:text-indigo-300">Visit Website &rarr;</a>}
                        </p>

                        {/* Key Metrics Summary */}
                        {(() => {
                            const metrics = getKeyMetrics(company);
                            const rows = [
                                { label: 'Total Revenue', value: metrics.totalRevenue },
                                { label: 'Net Income', value: metrics.netIncome },
                                { label: 'Net Profit Margin', value: metrics.netProfitMargin, isPercent: true },
                                { label: 'Diluted EPS', value: metrics.dilutedEPS },
                                { label: 'Cash & Equivalents', value: metrics.cashAndEquivalents },
                                { label: 'Total Debt', value: metrics.totalDebt },
                                { label: 'Op. Cash Flow', value: metrics.operatingCashFlow },
                                { label: 'Free Cash Flow', value: metrics.freeCashFlow },
                            ];

                            return (
                                <div className="mt-8 pt-8 border-t border-white/10">
                                    <div className="flex justify-between items-end mb-6">
                                        <div>
                                            <h4 className="text-xl font-bold text-white flex items-center gap-2">
                                                <BarChart3 className="text-indigo-400" size={24} />
                                                Key Financial Metrics
                                            </h4>
                                            <div className="text-xs text-gray-400 mt-1 pl-8">Snapshot of latest available data</div>
                                        </div>
                                        <div className="text-right flex items-end gap-3">
                                            <div>
                                                <div className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold mb-1">Latest Report</div>
                                                <div className="text-sm font-mono text-indigo-300 bg-indigo-500/10 px-3 py-1 rounded-full border border-indigo-500/20">
                                                    {latestReportDate || 'N/A'}
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                                        {rows.map(row => {
                                            let colorClass = "text-white";
                                            if (row.value !== null && row.value !== undefined) {
                                                if (row.value > 0) colorClass = "text-emerald-400";
                                                if (row.value < 0) colorClass = "text-rose-400";
                                            }
                                            if (row.label === 'Total Debt') colorClass = "text-gray-200";

                                            return (
                                                <div key={row.label} className="group relative p-5 rounded-2xl bg-gradient-to-br from-white/[0.03] to-white/[0.01] border border-white/5 hover:border-white/10 transition-all hover:bg-white/[0.05] hover:shadow-lg hover:shadow-black/20 hover:-translate-y-0.5">
                                                    <div className="text-[10px] text-gray-500 mb-2 font-bold tracking-widest uppercase opacity-70 group-hover:opacity-100 transition-opacity">{row.label}</div>
                                                    <div className={`text-xl font-mono font-bold ${colorClass} tracking-tight`}>
                                                        {row.isPercent ? formatPercent(row.value) : formatValue(row.value)}
                                                    </div>
                                                </div>
                                            )
                                        })}
                                    </div>
                                </div>
                            );
                        })()}
                    </GlassCard>
                )}

                {activeTab === 'analysis' && (
                    <div className="space-y-6">
                        {/* Current/Latest Analysis */}
                        {latestAnalysisReport && (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.5 }}
                            >
                                <AnalysisResultsView 
                                    report={latestAnalysisReport} 
                                    onReanalyze={() => setIsAnalyzeModalOpen(true)}
                                    onDelete={() => {
                                        if (confirm('Are you sure you want to delete this analysis report?')) {
                                            analysisApi.deleteReport(latestAnalysisReport.id)
                                                .then(() => fetchAnalysisReports())
                                                .catch(err => console.error(err));
                                        }
                                    }}
                                />
                            </motion.div>
                        )}

                        {/* New Analysis Button (when no current analysis) */}
                        {!latestAnalysisReport && (
                            <GlassCard className="text-center py-16">
                                <Sparkles size={48} className="mx-auto text-indigo-400 mb-4" />
                                <h3 className="text-xl font-semibold text-white mb-2">No Analysis Available</h3>
                                <p className="text-gray-400 mb-6">Run a company analysis to see detailed insights about this company.</p>
                                <GlassButton onClick={() => setIsAnalyzeModalOpen(true)} leftIcon={<Sparkles size={16}/>}>
                                    Analyze Company
                                </GlassButton>
                            </GlassCard>
                        )}

                        {/* Analysis History Section */}
                        <GlassCard>
                            <div className="flex items-center justify-between mb-6">
                                <div className="flex items-center gap-3">
                                    <Clock size={20} className="text-indigo-400" />
                                    <h3 className="text-lg font-semibold text-white">Analysis History</h3>
                                </div>
                                {latestAnalysisReport && (
                                    <GlassButton
                                        size="sm"
                                        variant="ghost"
                                        onClick={() => setIsAnalyzeModalOpen(true)}
                                        leftIcon={<Sparkles size={14}/>}
                                    >
                                        New Analysis
                                    </GlassButton>
                                )}
                            </div>

                            {/* Real History Items */}
                            <div className="space-y-3">
                                {analysisReports.length > 0 ? (
                                    analysisReports.map((report, idx) => {
                                        const isCurrent = idx === 0;
                                        return (
                                            <div
                                                key={report.id}
                                                className={`flex flex-col sm:flex-row gap-4 p-4 rounded-xl transition-colors ${
                                                    isCurrent
                                                    ? 'bg-indigo-500/10 border border-indigo-500/30'
                                                    : 'bg-white/5 border border-white/10 hover:bg-white/[0.07] cursor-pointer group'
                                                }`}
                                            >
                                                {/* Left Section: Rating & Time */}
                                                <div className="flex items-start gap-4 flex-1">
                                                    <div className="space-y-2">
                                                        <div className="flex items-center gap-3">
                                                            <RatingBadge rating={report.rating} />
                                                            {isCurrent && (
                                                                <span className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 px-2 py-1 rounded-full border border-emerald-500/20">
                                                                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                                                                    Current
                                                                </span>
                                                            )}
                                                        </div>
                                                        
                                                        <div className="flex flex-col">
                                                            <div className="flex items-center gap-2 text-sm text-gray-300 font-medium">
                                                                <Clock size={12} className="text-gray-500" />
                                                                {(() => {
                                                                    const dateStr = report.created_at.endsWith('Z') || report.created_at.includes('+') 
                                                                        ? report.created_at 
                                                                        : report.created_at + 'Z';
                                                                    
                                                                    let date = new Date(dateStr);
                                                                    const now = new Date();
                                                                    // Fix: If date is > 7 hours in the future (timezone mismatch artifact), subtract 8 hours
                                                                    if (date.getTime() - now.getTime() > 1000 * 60 * 60 * 7) {
                                                                        date = new Date(date.getTime() - 1000 * 60 * 60 * 8);
                                                                    }

                                                                    return formatDistanceToNow(date, { addSuffix: true });
                                                                })()}
                                                            </div>
                                                            <div className="text-xs text-gray-500 pl-5">
                                                                {(() => {
                                                                    const dateStr = report.created_at.endsWith('Z') || report.created_at.includes('+') 
                                                                        ? report.created_at 
                                                                        : report.created_at + 'Z';
                                                                    
                                                                    let date = new Date(dateStr);
                                                                    const now = new Date();
                                                                    // Fix: If date is > 7 hours in the future, subtract 8 hours
                                                                    if (date.getTime() - now.getTime() > 1000 * 60 * 60 * 7) {
                                                                        date = new Date(date.getTime() - 1000 * 60 * 60 * 8);
                                                                    }
                                                                        
                                                                    return format(date, "d MMM yyyy, h:mm a");
                                                                })()}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* Right Section: Confidence & Actions */}
                                                <div className="flex items-center justify-between sm:justify-end gap-6 sm:pl-4 border-t sm:border-t-0 border-white/5 pt-4 sm:pt-0">
                                                    <div className="text-left sm:text-right">
                                                        <div className={`text-sm font-medium ${report.confidence_score >= 80 ? 'text-emerald-400' : 'text-amber-400'}`}>
                                                            {report.confidence_score}% Confidence
                                                        </div>
                                                        <div className="text-xs text-gray-500">AI Analysis Model</div>
                                                    </div>
                                                    
                                                    <div className="flex items-center">
                                                        <button
                                                            onClick={(e) => handleDeleteReport(report.id, e)}
                                                            className="p-2 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-colors opacity-0 group-hover:opacity-100"
                                                            title="Delete report"
                                                        >
                                                            <Trash2 size={16} />
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })
                                ) : (
                                    <div className="text-center py-8 text-gray-500">
                                        <Clock size={32} className="mx-auto mb-3 opacity-50" />
                                        <p>No past analyses found.</p>
                                        <p className="text-sm mt-1">Run your first analysis to get started.</p>
                                    </div>
                                )}
                            </div>
                        </GlassCard>
                    </div>
                )}

                {activeTab === 'uploads' && (
                    <GlassCard>
                        <CompanyDocumentUpload companyId={company.id} companyTicker={company.ticker} />
                    </GlassCard>
                )}

                {activeTab === 'annual-reports' && (
                    <div className="space-y-4">
                        {loadingReports ? (
                            <GlassCard className="p-12">
                                <div className="flex items-center justify-center">
                                    <Loader2 className="animate-spin text-indigo-500" size={32} />
                                </div>
                            </GlassCard>
                        ) : annualReports.length === 0 ? (
                            <GlassCard className="p-12 text-center">
                                <FileDown size={48} className="mx-auto text-gray-500 mb-4" />
                                <p className="text-gray-400">No annual reports found for {company.name}.</p>
                            </GlassCard>
                        ) : (
                            annualReports.map((report) => (
                                <GlassCard
                                    key={report.id}
                                    className="p-6 hover:border-indigo-500/30 transition-colors"
                                >
                                    <div className="flex justify-between items-start mb-4">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-3 mb-2">
                                                <div className="flex items-center gap-2 text-xs font-semibold px-2 py-1 rounded bg-indigo-500/10 text-indigo-400 uppercase tracking-wider">
                                                    <FileDown size={12} />
                                                    Annual Report
                                                </div>
                                            </div>
                                            <h3 className="text-lg font-bold text-white mb-1">{report.title}</h3>
                                        </div>
                                        <span className="text-sm text-gray-400 flex items-center gap-1 ml-4 whitespace-nowrap">
                                            <Clock size={14} /> {report.date}
                                        </span>
                                    </div>

                                    <div className="flex justify-end">
                                        {report.link && (
                                            <a
                                                href={report.link}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-medium flex items-center gap-2 transition-colors"
                                            >
                                                View Announcement <ExternalLink size={16} />
                                            </a>
                                        )}
                                    </div>
                                </GlassCard>
                            ))
                        )}
                    </div>
                )}

                {/* Financials */}
                {activeTab === 'is' && renderFinancialSection('Income Statement', incomeStatement, IS_ORDER, isDate)}
                {activeTab === 'bs' && renderFinancialSection('Balance Sheet', balanceSheet, BS_ORDER, bsDate)}
                {activeTab === 'cf' && renderFinancialSection('Cash Flow', cashFlow, CF_ORDER, cfDate)}
            </div>

            <AnalysisWizardModal 
                isOpen={isAnalyzeModalOpen}
                onClose={() => setIsAnalyzeModalOpen(false)}
                onComplete={handleAnalysisComplete}
                companyName={company.name}
                companyId={company.id}
            />
        </div>
    );
}
