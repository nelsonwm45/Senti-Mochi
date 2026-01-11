'use client';

import { cn } from '@/lib/utils';
import { GlassCard } from './GlassCard';

interface GlassSkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  width?: string | number;
  height?: string | number;
  className?: string;
  variant?: 'card' | 'text' | 'circular';
}

export function GlassSkeleton({
  width,
  height,
  className,
  variant = 'text',
  ...props
}: GlassSkeletonProps) {
  const baseClasses = cn(
    'relative overflow-hidden bg-glass-border/30 rounded-lg',
    'after:absolute after:inset-0 after:-translate-x-full',
    'after:animate-[shimmer_1.5s_infinite]',
    'after:bg-gradient-to-r after:from-transparent after:via-white/10 after:to-transparent',
    className
  );

  if (variant === 'card') {
    return (
      <GlassCard className={cn('w-full', className)}>
        <div 
          className={cn(baseClasses, 'w-full h-full rounded-none bg-transparent')} 
          style={{ width, height }}
          {...props}
        />
      </GlassCard>
    );
  }

  return (
    <div
      className={cn(
        baseClasses,
        variant === 'circular' && 'rounded-full'
      )}
      style={{ width, height }}
      {...props}
    />
  );
}
