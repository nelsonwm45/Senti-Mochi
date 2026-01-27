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
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-xl bg-red-500/10">
            <ShieldCheck className="text-red-500" size={24} />
          </div>
          <h1 className="text-3xl font-bold text-foreground">Credit Risk Dashboard</h1>
        </div>
        <p className="text-foreground-muted">Monitor credit risk, debt ratios, and financial stability indicators</p>
      </motion.div>

      {/* Risk Metrics */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-3 gap-6"
      >
        {riskMetrics.map((metric, index) => {
          const isRed = metric.color === 'red';
          const borderColor = isRed ? 'border-red-500/20 hover:border-red-500/50' : 'border-green-500/20 hover:border-green-500/50';
          const iconColor = isRed ? 'text-red-500' : 'text-green-500';

          return (
            <motion.div
              key={index}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3, delay: 0.1 + index * 0.05 }}
            >
              <GlassCard className={`p-6 border ${borderColor} transition-colors`}>
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <p className="text-sm text-foreground-muted mb-1">{metric.label}</p>
                    <p className="text-2xl font-bold text-foreground">{metric.value}</p>
                  </div>
                  <div className={iconColor}>
                    <ShieldCheck size={20} />
                  </div>
                </div>
                <p className="text-xs text-foreground-muted">{metric.subtitle}</p>
              </GlassCard>
            </motion.div>
          );
        })}
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

export default CreditRiskLayout;
