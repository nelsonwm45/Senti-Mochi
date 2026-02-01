'use client';

import { ReactNode } from 'react';
import { motion } from 'framer-motion';
import { ShieldCheck } from 'lucide-react';
import { GlassCard } from '@/components/ui/GlassCard';

interface CreditRiskLayoutProps {
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

export function CreditRiskLayout({ stats, feedComponent, chartComponent }: CreditRiskLayoutProps) {
    const riskMetrics = [
        {
            label: 'Risk Score',
            value: '32/100',
            trend: 'stable',
            subtitle: 'Overall credit risk (lower is better)',
            color: 'green'
        },
        {
            label: 'Debt/Equity',
            value: '0.68',
            trend: 'stable',
            subtitle: 'Leverage ratio',
            color: 'green'
        },
        {
            label: 'Red Flags',
            value: '2',
            trend: 'down',
            subtitle: 'Warning indicators detected',
            color: 'red'
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

export default CreditRiskLayout;
