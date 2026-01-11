'use client';

import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sun, Moon, Monitor } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ThemeToggleProps {
  variant?: 'button' | 'switch' | 'dropdown';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function ThemeToggle({ variant = 'button', size = 'md', className }: ThemeToggleProps) {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className={cn(
        'rounded-xl bg-glass-bg animate-pulse',
        size === 'sm' && 'w-8 h-8',
        size === 'md' && 'w-10 h-10',
        size === 'lg' && 'w-12 h-12',
        className
      )} />
    );
  }

  const iconSize = size === 'sm' ? 16 : size === 'md' ? 20 : 24;

  if (variant === 'button') {
    return (
      <motion.button
        onClick={() => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')}
        className={cn(
          'relative flex items-center justify-center rounded-xl',
          'bg-glass-bg backdrop-blur-glass border border-glass-border',
          'text-foreground-secondary hover:text-accent',
          'transition-colors duration-200',
          'focus:outline-none focus:ring-2 focus:ring-accent/50',
          size === 'sm' && 'w-8 h-8',
          size === 'md' && 'w-10 h-10',
          size === 'lg' && 'w-12 h-12',
          className
        )}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        aria-label={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} mode`}
      >
        <AnimatePresence mode="wait">
          {resolvedTheme === 'dark' ? (
            <motion.div
              key="moon"
              initial={{ rotate: -90, opacity: 0 }}
              animate={{ rotate: 0, opacity: 1 }}
              exit={{ rotate: 90, opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <Moon size={iconSize} />
            </motion.div>
          ) : (
            <motion.div
              key="sun"
              initial={{ rotate: 90, opacity: 0 }}
              animate={{ rotate: 0, opacity: 1 }}
              exit={{ rotate: -90, opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <Sun size={iconSize} />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.button>
    );
  }

  if (variant === 'switch') {
    return (
      <motion.button
        onClick={() => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')}
        className={cn(
          'relative flex items-center rounded-full',
          'bg-glass-bg backdrop-blur-glass border border-glass-border',
          'p-1 cursor-pointer',
          'focus:outline-none focus:ring-2 focus:ring-accent/50',
          size === 'sm' && 'w-14 h-7',
          size === 'md' && 'w-16 h-8',
          size === 'lg' && 'w-20 h-10',
          className
        )}
        aria-label={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} mode`}
      >
        <motion.div
          className={cn(
            'absolute flex items-center justify-center rounded-full',
            'bg-accent text-white shadow-lg',
            size === 'sm' && 'w-5 h-5',
            size === 'md' && 'w-6 h-6',
            size === 'lg' && 'w-8 h-8',
          )}
          animate={{
            x: resolvedTheme === 'dark'
              ? (size === 'sm' ? 28 : size === 'md' ? 32 : 40)
              : 0
          }}
          transition={{ type: 'spring', stiffness: 500, damping: 30 }}
        >
          {resolvedTheme === 'dark' ? (
            <Moon size={iconSize - 4} />
          ) : (
            <Sun size={iconSize - 4} />
          )}
        </motion.div>
        <div className="flex items-center justify-between w-full px-1">
          <Sun size={iconSize - 6} className="text-foreground-muted" />
          <Moon size={iconSize - 6} className="text-foreground-muted" />
        </div>
      </motion.button>
    );
  }

  // Dropdown variant
  return (
    <div className={cn('relative', className)}>
      <div className="flex items-center gap-1 p-1 rounded-xl bg-glass-bg backdrop-blur-glass border border-glass-border">
        {[
          { value: 'light', icon: Sun, label: 'Light' },
          { value: 'dark', icon: Moon, label: 'Dark' },
          { value: 'system', icon: Monitor, label: 'System' },
        ].map(({ value, icon: Icon, label }) => (
          <motion.button
            key={value}
            onClick={() => setTheme(value)}
            className={cn(
              'relative flex items-center justify-center rounded-lg p-2',
              'transition-colors duration-200',
              'focus:outline-none',
              theme === value
                ? 'text-accent'
                : 'text-foreground-muted hover:text-foreground-secondary'
            )}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            aria-label={label}
          >
            {theme === value && (
              <motion.div
                layoutId="theme-indicator"
                className="absolute inset-0 rounded-lg bg-accent/10"
                transition={{ type: 'spring', stiffness: 500, damping: 30 }}
              />
            )}
            <Icon size={iconSize - 2} className="relative z-10" />
          </motion.button>
        ))}
      </div>
    </div>
  );
}

export default ThemeToggle;
