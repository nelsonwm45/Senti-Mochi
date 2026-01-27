'use client';

import { ReactNode } from 'react';
import { motion } from 'framer-motion';
import { BarChart3 } from 'lucide-react';
import { GlassCard } from '@/components/ui/GlassCard';

interface MarketAnalystLayoutProps {
    stats: {
        bursa: number;
        star: number;
        nst: number;
        edge: number;
        total: number;
    };
    feedComponent: ReactNode;
    chartComponent: ReactNode;
}

export function MarketAnalystLayout({ stats, feedComponent, chartComponent }: MarketAnalystLayoutProps) {
    const analystMetrics = [
        {
            label: 'Market Position',
            value: '#3',
            trend: 'up',
            subtitle: 'Sector ranking',
            color: 'amber'
        },
        {
            label: 'Valuation',
            value: '12.5x',
            trend: 'up',
            subtitle: 'Current P/E ratio',
            color: 'amber'
        },
        {
            label: 'Market Share',
            value: '18.2%',
            trend: 'up',
            subtitle: 'Industry percentage',
            color: 'amber'
        }
    ];

    return (
        <div className="space-y-8">
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
            >
                <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 rounded-xl bg-amber-500/10">
                        <BarChart3 className="text-amber-500" size={24} />
                    </div>
                    <h1 className="text-3xl font-bold text-foreground">Market Analysis Dashboard</h1>
                </div>
                <p className="text-foreground-muted">Analyze market position, valuation metrics, and competitive landscape</p>
            </motion.div>

            {/* Analyst Metrics */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.1 }}
                className="grid grid-cols-1 md:grid-cols-3 gap-6"
            >
                {analystMetrics.map((metric, index) => (
                    <motion.div
                        key={index}
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.3, delay: 0.1 + index * 0.05 }}
                    >
                        <GlassCard className="p-6 border border-amber-500/20 hover:border-amber-500/50 transition-colors">
                            <div className="flex items-start justify-between mb-4">
                                <div>
                                    <p className="text-sm text-foreground-muted mb-1">{metric.label}</p>
                                    <p className="text-2xl font-bold text-foreground">{metric.value}</p>
                                </div>
                                <div className="text-amber-500">
                                    <BarChart3 size={20} />
                                </div>
                            </div>
                            <p className="text-xs text-foreground-muted">{metric.subtitle}</p>
                        </GlassCard>
                    </motion.div>
                ))}
            </motion.div>

            {/* Main Content Grid */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.2 }}
                className="grid grid-cols-1 lg:grid-cols-3 gap-8"
            >
                {/* Feed - 2/3 width */}
                <div className="lg:col-span-2">
                    {feedComponent}
                </div>

                {/* Chart - 1/3 width */}
                <div>
                    {chartComponent}
                </div>
            </motion.div>
        </div>
    );
}

export default MarketAnalystLayout;
