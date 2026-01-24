import { useState } from 'react';
import { motion } from 'framer-motion';
import { Check, Briefcase, Glasses, Users, LineChart } from 'lucide-react';
import { cn } from '@/lib/utils';
import { UserRole } from '@/lib/api/analysis';

interface RoleSelectorProps {
    selectedRole: UserRole;
    onSelect: (role: UserRole) => void;
}

export function RoleSelector({ selectedRole, onSelect }: RoleSelectorProps) {
    const roles: { id: UserRole; label: string; icon: any; desc: string; color: string }[] = [
        { 
            id: 'investor', 
            label: 'Retail Investor', 
            icon: Glasses, 
            desc: 'Focus on growth potential, market sentiment, and long-term value.',
            color: 'emerald'
        },
        { 
            id: 'credit_risk', 
            label: 'Credit Risk Officer', 
            icon: Briefcase, 
            desc: 'Focus on debt servicing, liquidity, covenants, and downside protection.',
            color: 'amber'
        },
        { 
            id: 'relationship_manager', 
            label: 'Relationship Manager', 
            icon: Users, 
            desc: 'Focus on strategic alignment, cross-selling opportunities, and client needs.',
            color: 'blue'
        },
        { 
            id: 'market_analyst', 
            label: 'Market Analyst', 
            icon: LineChart, 
            desc: 'Focus on valuation models, competitive landscape, and quality of earnings.',
            color: 'purple'
        }
    ];

    return (
        <div className="space-y-4">
            <h3 className="text-white font-semibold">Select Analysis Persona</h3>
            <div className="grid gap-3">
                {roles.map((role) => {
                    const isSelected = selectedRole === role.id;
                    return (
                        <button
                            key={role.id}
                            onClick={() => onSelect(role.id)}
                            className={cn(
                                "flex items-start gap-4 p-4 rounded-xl border transition-all text-left group relative overflow-hidden",
                                isSelected 
                                    ? `bg-${role.color}-500/10 border-${role.color}-500/50`
                                    : "bg-white/5 border-white/10 hover:bg-white/[0.07] hover:border-white/20"
                            )}
                        >
                            <div className={cn(
                                "w-10 h-10 rounded-lg flex items-center justify-center transition-colors mt-0.5",
                                isSelected ? `bg-${role.color}-500 text-white` : `bg-white/5 text-gray-400 group-hover:text-${role.color}-400`
                            )}>
                                <role.icon size={20} />
                            </div>
                            <div className="flex-1">
                                <div className="font-semibold text-white flex items-center justify-between">
                                    {role.label}
                                    {isSelected && <Check size={18} className={`text-${role.color}-500`} />}
                                </div>
                                <div className="text-sm text-gray-400 mt-1 leading-snug">{role.desc}</div>
                            </div>
                            {isSelected && (
                                <motion.div 
                                    layoutId="role-outline"
                                    className={`absolute inset-0 border-2 border-${role.color}-500 rounded-xl`}
                                    initial={false}
                                    transition={{ type: "spring", stiffness: 500, damping: 30 }}
                                />
                            )}
                        </button>
                    );
                })}
            </div>
        </div>
    );
}
