'use client';

import { ReactNode } from 'react';
import { motion } from 'framer-motion';
import { Users } from 'lucide-react';
import { GlassCard } from '@/components/ui/GlassCard';

interface RelationshipManagerLayoutProps {
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

export function RelationshipManagerLayout({ stats, feedComponent, chartComponent }: RelationshipManagerLayoutProps) {
    const rmMetrics = [
        {
            label: 'Engagement Opportunities',
            value: '24',
            trend: 'up',
            subtitle: 'Active client touchpoints',
            color: 'blue'
        },
        {
            label: 'Quarterly Results',
            value: '↑ Q4',
            trend: 'up',
            subtitle: 'Latest performance period',
            color: 'blue'
        },
        {
            label: 'Client Sentiment',
            value: '+8.2%',
            trend: 'up',
            subtitle: 'Positive sentiment trend',
            color: 'blue'
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

export default RelationshipManagerLayout;
