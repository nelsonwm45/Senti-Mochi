'use client';

import ProtectedLayout from '@/components/layouts/ProtectedLayout';
import { useTheme } from 'next-themes';
import { Moon, Sun, Monitor, User, Settings as SettingsIcon } from 'lucide-react';
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { GlassCard } from '@/components/ui/GlassCard';

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // Prevent hydration mismatch
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  const themeOptions = [
    { id: 'light', label: 'Light', icon: Sun },
    { id: 'dark', label: 'Dark', icon: Moon },
    { id: 'system', label: 'System', icon: Monitor },
  ];

  return (
    <ProtectedLayout>
      <div className="min-h-full p-4 md:p-8">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center space-x-4 mb-8"
          >
            <div className="p-3 bg-gradient-brand rounded-xl shadow-lg shadow-accent/20">
              <SettingsIcon className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-brand bg-clip-text text-transparent">
                Settings
              </h1>
              <p className="text-foreground-muted">
                Manage your preferences and account settings
              </p>
            </div>
          </motion.div>

          <div className="space-y-6">
            {/* Profile Placeholder */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
            >
              <GlassCard className="overflow-hidden opacity-75 grayscale hover:grayscale-0 transition-all duration-500">
                <div className="px-6 py-4 border-b border-glass-border bg-glass-bg/50">
                  <h2 className="text-lg font-semibold text-foreground flex items-center">
                    <User className="w-5 h-5 mr-3 text-accent" />
                    Profile Settings
                  </h2>
                </div>
                <div className="p-8 text-center">
                  <div className="w-16 h-16 bg-glass-border rounded-full flex items-center justify-center mx-auto mb-4">
                    <SettingsIcon className="w-8 h-8 text-foreground-muted animate-spin-slow" />
                  </div>
                  <h3 className="text-lg font-medium text-foreground mb-2">Coming Soon</h3>
                  <p className="text-foreground-muted max-w-sm mx-auto">
                    Advanced profile management features are currently under development. Stay tuned!
                  </p>
                </div>
              </GlassCard>
            </motion.div>
          </div>
        </div>
      </div>
    </ProtectedLayout>
  );
}
