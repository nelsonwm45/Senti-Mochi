'use client';

import { cn } from '@/lib/utils';

type BadgeVariant = 'default' | 'success' | 'warning' | 'error' | 'info' | 'accent';
type BadgeSize = 'sm' | 'md' | 'lg';

interface GlassBadgeProps {
  variant?: BadgeVariant;
  size?: BadgeSize;
  dot?: boolean;
  icon?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

const variantClasses = {
  default: 'glass-badge',
  success: 'glass-badge-success',
  warning: 'glass-badge-warning',
  error: 'glass-badge-error',
  info: 'glass-badge-info',
  accent: `
    bg-accent/10 text-accent border-accent/20
    border rounded-full
  `,
};

const sizeClasses = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-xs',
  lg: 'px-3 py-1.5 text-sm',
};

const dotSizeClasses = {
  sm: 'w-1.5 h-1.5',
  md: 'w-2 h-2',
  lg: 'w-2.5 h-2.5',
};

const dotColorClasses = {
  default: 'bg-foreground-muted',
  success: 'bg-green-500',
  warning: 'bg-yellow-500',
  error: 'bg-red-500',
  info: 'bg-blue-500',
  accent: 'bg-accent',
};

export function GlassBadge({
  variant = 'default',
  size = 'md',
  dot = false,
  icon,
  children,
  className,
}: GlassBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 font-medium',
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
    >
      {dot && (
        <span
          className={cn(
            'rounded-full animate-pulse',
            dotSizeClasses[size],
            dotColorClasses[variant]
          )}
        />
      )}
      {icon && <span className="shrink-0">{icon}</span>}
      {children}
    </span>
  );
}

// Status-specific badge presets
export function StatusBadge({
  status,
  size = 'md',
  className,
}: {
  status: 'pending' | 'processing' | 'ready' | 'failed' | 'success';
  size?: BadgeSize;
  className?: string;
}) {
  const statusConfig = {
    pending: { variant: 'default' as const, label: 'Pending', dot: true },
    processing: { variant: 'warning' as const, label: 'Processing', dot: true },
    ready: { variant: 'success' as const, label: 'Ready', dot: false },
    failed: { variant: 'error' as const, label: 'Failed', dot: false },
    success: { variant: 'success' as const, label: 'Success', dot: false },
  };

  const config = statusConfig[status];

  return (
    <GlassBadge
      variant={config.variant}
      size={size}
      dot={config.dot}
      className={className}
    >
      {config.label}
    </GlassBadge>
  );
}

export default GlassBadge;
