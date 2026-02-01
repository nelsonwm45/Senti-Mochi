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
