import React, { useState } from 'react';
import { GlassCard } from '@/components/ui/GlassCard';
import { GlassButton } from '@/components/ui/GlassButton';
import { Sparkles, Plus, Trash2, Save, RefreshCw, MessageSquare, Briefcase, Zap, TrendingUp, AlertCircle, FileText } from 'lucide-react';
import { TalkingPoints as TalkingPointsType, analysisApi, AnalysisReport } from '@/lib/api/analysis';
import { motion, AnimatePresence } from 'framer-motion';

interface TalkingPointsProps {
    report: AnalysisReport;
    onUpdate: () => void;
}

export function TalkingPoints({ report, onUpdate }: TalkingPointsProps) {
    const [loading, setLoading] = useState(false);
    const [talkingPoints, setTalkingPoints] = useState<TalkingPointsType>(report.talking_points || {});
    const [isEditing, setIsEditing] = useState(false);
    const [editData, setEditData] = useState<TalkingPointsType>(report.talking_points || {});

    const hasData = Object.keys(talkingPoints).length > 0;

    const handleGenerate = async () => {
        setLoading(true);
        try {
            const data = await analysisApi.generateTalkingPoints(report.id);
            setTalkingPoints(data);
            setEditData(data);
            onUpdate();
        } catch (error) {
            console.error("Failed to generate talking points:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        setLoading(true);
        try {
            const data = await analysisApi.updateTalkingPoints(report.id, editData);
            setTalkingPoints(data);
            setIsEditing(false);
            onUpdate();
        } catch (error) {
            console.error("Failed to save talking points:", error);
        } finally {
            setLoading(false);
        }
    };

    const SectionHeader = ({ icon: Icon, title, description }: { icon: any, title: string, description?: string }) => (
        <div className="flex items-center gap-3 mb-4 border-b border-white/10 pb-2">
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
                <Icon size={18} />
            </div>
            <div>
                <h3 className="text-lg font-semibold text-white">{title}</h3>
                {description && <p className="text-xs text-gray-400">{description}</p>}
            </div>
        </div>
    );

    const EditableText = ({ 
        value, 
        onChange, 
        label, 
        placeholder 
    }: { 
        value?: string, 
        onChange: (val: string) => void, 
        label?: string,
        placeholder?: string 
    }) => {
        if (isEditing) {
            return (
                <div className="mb-3">
                    {label && <label className="text-xs text-gray-400 mb-1 block uppercase tracking-wider">{label}</label>}
                    <textarea
                        className="w-full bg-white/5 border border-white/10 rounded-lg p-3 text-white focus:outline-none focus:border-indigo-500/50 min-h-[80px]"
                        value={value || ''}
                        onChange={(e) => onChange(e.target.value)}
                        placeholder={placeholder || "Enter text..."}
                    />
                </div>
            );
        }
        if (!value) return null;
        return (
            <div className="mb-3">
                {label && <label className="text-xs text-gray-500 mb-1 block uppercase tracking-wider">{label}</label>}
                <p className="text-gray-200 leading-relaxed bg-white/[0.02] p-3 rounded-lg border border-white/5">{value}</p>
            </div>
        );
    };

    const EditableList = ({ 
        items, 
        onChange 
    }: { 
        items?: string[], 
        onChange: (items: string[]) => void 
    }) => {
        const list = items || [];

        if (isEditing) {
            return (
                <div className="space-y-2">
                    {list.map((item, idx) => (
                        <div key={idx} className="flex gap-2">
                            <input
                                className="flex-1 bg-white/5 border border-white/10 rounded-lg p-2 text-white focus:outline-none focus:border-indigo-500/50"
                                value={item}
                                onChange={(e) => {
                                    const newItems = [...list];
                                    newItems[idx] = e.target.value;
                                    onChange(newItems);
                                }}
                            />
                            <button
                                onClick={() => onChange(list.filter((_, i) => i !== idx))}
                                className="p-2 hover:bg-red-500/20 text-red-400 rounded-lg transition-colors"
                            >
                                <Trash2 size={16} />
                            </button>
                        </div>
                    ))}
                    <button
                        onClick={() => onChange([...list, ""])}
                        className="flex items-center gap-2 text-sm text-indigo-400 hover:text-indigo-300 mt-2"
                    >
                        <Plus size={14} /> Add Item
                    </button>
                </div>
            );
        }

        if (!list.length) return <p className="text-sm text-gray-500 italic">No items listed.</p>;

        return (
            <ul className="space-y-2">
                {list.map((item, idx) => (
                    <li key={idx} className="flex gap-3 text-gray-300">
                        <span className="text-indigo-500 mt-1.5">•</span>
                        <span>{item}</span>
                    </li>
                ))}
            </ul>
        );
    };

    if (!hasData && !loading) {
        return (
            <GlassCard className="text-center py-16">
                <MessageSquare size={48} className="mx-auto text-indigo-400 mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">No Talking Points Available</h3>
                <p className="text-gray-400 mb-6 max-w-md mx-auto">
                    Generate structured talking points for client meetings based on the latest analysis.
                </p>
                <GlassButton onClick={handleGenerate} leftIcon={<Sparkles size={16} />}>
                    Generate Talking Points
                </GlassButton>
            </GlassCard>
        );
    }

    if (loading) {
        return (
            <GlassCard className="flex items-center justify-center py-24">
                <div className="text-center">
                    <RefreshCw className="animate-spin text-indigo-500 mx-auto mb-4" size={32} />
                    <p className="text-gray-400">Processing...</p>
                </div>
            </GlassCard>
        );
    }

    // Render Data View
    const data = isEditing ? editData : talkingPoints;

    return (
        <div className="space-y-6">
            <div className="flex justify-end gap-3">
                {isEditing ? (
                    <>
                        <GlassButton 
                            variant="ghost" 
                            size="sm" 
                            onClick={() => {
                                setEditData(talkingPoints);
                                setIsEditing(false);
                            }}
                        >
                            Cancel
                        </GlassButton>
                        <GlassButton 
                            variant="primary" 
                            size="sm" 
                            onClick={handleSave} 
                            leftIcon={<Save size={14} />}
                        >
                            Save Changes
                        </GlassButton>
                    </>
                ) : (
                    <>
                        <GlassButton 
                            variant="ghost" 
                            size="sm" 
                            onClick={handleGenerate} 
                            leftIcon={<RefreshCw size={14} />}
                        >
                            Regenerate
                        </GlassButton>
                        <GlassButton 
                            variant="secondary" 
                            size="sm" 
                            onClick={() => {
                                setEditData(JSON.parse(JSON.stringify(talkingPoints)));
                                setIsEditing(true);
                            }}
                            leftIcon={<FileText size={14} />}
                        >
                            Edit Notes
                        </GlassButton>
                    </>
                )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* 1. Headline Summary */}
                <GlassCard className="col-span-1 md:col-span-2 bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border-indigo-500/20">
                    <SectionHeader icon={Briefcase} title="Headline Summary" description="Instant orientation: Client tone and direction." />
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <EditableText 
                            label="Overall Client Tone"
                            value={data.headline_summary?.overall_tone} 
                            onChange={(val) => setEditData({...data, headline_summary: { ...data.headline_summary!, overall_tone: val }})}
                        />
                        <EditableText 
                            label="Direction of Change"
                             value={data.headline_summary?.direction_of_change} 
                            onChange={(val) => setEditData({...data, headline_summary: { ...data.headline_summary!, direction_of_change: val }})}
                        />
                    </div>
                </GlassCard>

                {/* 2. Key Developments */}
                <GlassCard>
                    <SectionHeader icon={TrendingUp} title="Key Developments" description="Recent, factual changes." />
                    <EditableList 
                        items={data.key_developments} 
                        onChange={(items) => setEditData({...data, key_developments: items})} 
                    />
                </GlassCard>

                {/* 4. Conversation Starters */}
                <GlassCard>
                    <SectionHeader icon={MessageSquare} title="Conversation Starters" description="Open-ended engagement questions." />
                    <EditableList 
                        items={data.conversation_starters} 
                        onChange={(items) => setEditData({...data, conversation_starters: items})} 
                    />
                </GlassCard>

                {/* 3. Business Implications */}
                <GlassCard className="col-span-1 md:col-span-2">
                    <SectionHeader icon={AlertCircle} title="Business Implications" description="Impact on operations and strategy." />
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <EditableText 
                            label="Operational Impact"
                            value={data.business_implications?.operational_impact} 
                            onChange={(val) => setEditData({...data, business_implications: { ...data.business_implications!, operational_impact: val }})}
                        />
                        <EditableText 
                            label="Financial Impact"
                            value={data.business_implications?.financial_pressure_or_upside} 
                            onChange={(val) => setEditData({...data, business_implications: { ...data.business_implications!, financial_pressure_or_upside: val }})}
                        />
                        <EditableText 
                            label="Strategic Implications"
                            value={data.business_implications?.strategic_implications} 
                            onChange={(val) => setEditData({...data, business_implications: { ...data.business_implications!, strategic_implications: val }})}
                        />
                    </div>
                </GlassCard>

                {/* 5. Opportunity Angles */}
                <GlassCard className="col-span-1 md:col-span-2">
                    <SectionHeader icon={Zap} title="Opportunity Angles" description="Bank value creation opportunities." />
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <EditableText 
                            label="Financing"
                            value={data.opportunity_angles?.financing} 
                            onChange={(val) => setEditData({...data, opportunity_angles: { ...data.opportunity_angles!, financing: val }})}
                        />
                         <EditableText 
                            label="Risk Management"
                            value={data.opportunity_angles?.risk_management} 
                            onChange={(val) => setEditData({...data, opportunity_angles: { ...data.opportunity_angles!, risk_management: val }})}
                        />
                        <EditableText 
                            label="Advisory"
                            value={data.opportunity_angles?.advisory} 
                            onChange={(val) => setEditData({...data, opportunity_angles: { ...data.opportunity_angles!, advisory: val }})}
                        />
                    </div>
                </GlassCard>

                {/* 6. Others */}
                <GlassCard className="col-span-1 md:col-span-2">
                     <SectionHeader icon={FileText} title="Notes & Miscellaneous" />
                     <EditableText 
                        value={data.others} 
                        onChange={(val) => setEditData({...data, others: val})}
                        placeholder="Additional notes..."
                    />
                </GlassCard>
            </div>
        </div>
    );
}
