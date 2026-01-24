import { DebateSynthesis } from '@/lib/api/analysis';
import { GlassCard } from '@/components/ui/GlassCard';
import { TrendingUp, TrendingDown, Swords } from 'lucide-react';

export function DebateSynthesisView({ debate }: { debate: DebateSynthesis }) {
    if (!debate) return null;

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
            {/* Bull Case */}
            <GlassCard className="h-full border-t-4 border-t-emerald-500 bg-gradient-to-b from-emerald-900/10 to-transparent">
                <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-400">
                        <TrendingUp size={20} />
                    </div>
                    <h3 className="font-bold text-white text-xl">Bull Arguments</h3>
                </div>
                <ul className="space-y-3">
                    {debate.bull_arguments?.map((arg, i) => (
                        <li key={i} className="flex gap-3 text-sm text-gray-300 p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/10">
                            <span className="text-emerald-500 font-bold">•</span>
                            {arg}
                        </li>
                    ))}
                </ul>
            </GlassCard>

             {/* Clashes / Middle Ground */}
             <div className="h-full flex flex-col">
                 <div className="flex items-center justify-center gap-2 text-gray-400 text-sm font-medium uppercase tracking-wider mb-4 mt-2 lg:hidden">
                    <Swords size={16} /> Evidence Clashes
                 </div>
                 
                 <GlassCard className="border-t-4 border-t-indigo-500 flex-1">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="w-10 h-10 rounded-full bg-indigo-500/20 flex items-center justify-center text-indigo-400">
                            <Swords size={20} />
                        </div>
                        <h3 className="font-bold text-white text-xl">Key Friction Points</h3>
                    </div>
                     <ul className="space-y-3">
                        {debate.evidence_clashes?.map((clash, i) => (
                            <li key={i} className="text-sm text-indigo-200 p-3 rounded-lg bg-indigo-500/5 border border-indigo-500/10 italic">
                                "{clash}"
                            </li>
                        ))}
                    </ul>
                 </GlassCard>
             </div>

            {/* Bear Case */}
            <GlassCard className="h-full border-t-4 border-t-red-500 bg-gradient-to-b from-red-900/10 to-transparent">
                <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center text-red-400">
                        <TrendingDown size={20} />
                    </div>
                    <h3 className="font-bold text-white text-xl">Bear Arguments</h3>
                </div>
                <ul className="space-y-3">
                    {debate.bear_arguments?.map((arg, i) => (
                        <li key={i} className="flex gap-3 text-sm text-gray-300 p-3 rounded-lg bg-red-500/5 border border-red-500/10">
                            <span className="text-red-500 font-bold">•</span>
                            {arg}
                        </li>
                    ))}
                </ul>
            </GlassCard>
        </div>
    );
}
