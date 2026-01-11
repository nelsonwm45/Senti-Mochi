'use client';

import { forwardRef, ButtonHTMLAttributes } from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'outline' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg' | 'icon';

interface GlassButtonProps extends Omit<HTMLMotionProps<'button'>, 'size'> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  children?: React.ReactNode;
}

const variantClasses = {
  primary: `
    bg-gradient-primary text-white
    shadow-lg shadow-accent/20
    hover:shadow-xl hover:shadow-accent/30
    hover:brightness-110
  `,
  secondary: `
    bg-glass-bg backdrop-blur-glass
    border border-glass-border
    text-foreground
    hover:bg-glass-bg hover:border-accent
    hover:text-accent
  `,
  ghost: `
    bg-transparent
    text-foreground-secondary
    hover:bg-accent/10 hover:text-accent
  `,
  outline: `
    bg-transparent
    border border-accent
    text-accent
    hover:bg-accent hover:text-white
  `,
  danger: `
    bg-gradient-to-r from-red-500 to-red-600 text-white
    shadow-lg shadow-red-500/20
    hover:shadow-xl hover:shadow-red-500/30
    hover:brightness-110
  `,
};

const sizeClasses = {
  sm: 'px-3 py-1.5 text-sm rounded-lg gap-1.5',
  md: 'px-4 py-2 text-sm rounded-xl gap-2',
  lg: 'px-6 py-3 text-base rounded-xl gap-2',
  icon: 'p-2.5 rounded-xl',
};

export const GlassButton = forwardRef<HTMLButtonElement, GlassButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      isLoading = false,
      leftIcon,
      rightIcon,
      className,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    return (
      <motion.button
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center font-semibold',
          'transition-all duration-200 ease-out',
          'focus:outline-none focus:ring-2 focus:ring-accent/50 focus:ring-offset-2 focus:ring-offset-background',
          'disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none',
          variantClasses[variant],
          sizeClasses[size],
          className
        )}
        disabled={disabled || isLoading}
        whileHover={{ scale: disabled || isLoading ? 1 : 1.02 }}
        whileTap={{ scale: disabled || isLoading ? 1 : 0.98 }}
        transition={{ duration: 0.1 }}
        {...props}
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          leftIcon
        )}
        {children}
        {!isLoading && rightIcon}
      </motion.button>
    );
  }
);

GlassButton.displayName = 'GlassButton';

export default GlassButton;
