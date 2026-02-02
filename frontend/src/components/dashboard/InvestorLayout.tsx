'use client';

import { ReactNode } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp } from 'lucide-react';
import { GlassCard } from '@/components/ui/GlassCard';

interface InvestorLayoutProps {
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

export function InvestorLayout({ stats, feedComponent, chartComponent }: InvestorLayoutProps) {
    const investorMetrics = [
        {
            label: 'Revenue Growth',
            value: '+12.5%',
            trend: 'up',
            subtitle: 'YoY growth',
            color: 'emerald'
        },
        {
            label: 'EPS',
            value: '₹45.20',
            trend: 'up',
            subtitle: 'Earnings per share',
            color: 'emerald'
        },
        {
            label: 'ROE',
            value: '18.3%',
            trend: 'up',
            subtitle: 'Return on equity',
            color: 'emerald'
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

export default InvestorLayout;
