'use client';

import { forwardRef, HTMLAttributes } from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';
import { cn } from '@/lib/utils';

type GlassCardVariant = 'default' | 'hover' | 'interactive' | 'static';

interface GlassCardProps extends HTMLMotionProps<'div'> {
  variant?: GlassCardVariant;
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  children: React.ReactNode;
}

const paddingClasses = {
  none: '',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6',
  xl: 'p-8',
};

const variantClasses = {
  default: 'glass-card',
  hover: 'glass-card hover:scale-[1.02]',
  interactive: 'glass-card cursor-pointer hover:scale-[1.02] active:scale-[0.98]',
  static: 'glass-card-static',
};

export const GlassCard = forwardRef<HTMLDivElement, GlassCardProps>(
  ({ variant = 'default', padding = 'lg', className, children, ...props }, ref) => {
    return (
      <motion.div
        ref={ref}
        className={cn(variantClasses[variant], paddingClasses[padding], className)}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
        {...props}
      >
        {children}
      </motion.div>
    );
  }
);

GlassCard.displayName = 'GlassCard';

// Static version without animation for SSR
export const GlassCardStatic = forwardRef<HTMLDivElement, Omit<GlassCardProps, keyof HTMLMotionProps<'div'>> & HTMLAttributes<HTMLDivElement>>(
  ({ variant = 'static', padding = 'lg', className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(variantClasses[variant], paddingClasses[padding], className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);

GlassCardStatic.displayName = 'GlassCardStatic';

export default GlassCard;
