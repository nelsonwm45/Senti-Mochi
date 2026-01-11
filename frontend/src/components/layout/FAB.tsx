'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface FABAction {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
}

interface FABProps {
  actions?: FABAction[];
  icon?: React.ReactNode;
  label?: string;
  onClick?: () => void;
  position?: 'bottom-right' | 'bottom-left' | 'bottom-center';
  className?: string;
}

const positionClasses = {
  'bottom-right': 'bottom-6 right-6',
  'bottom-left': 'bottom-6 left-6',
  'bottom-center': 'bottom-6 left-1/2 -translate-x-1/2',
};

export function FAB({
  actions,
  icon,
  label,
  onClick,
  position = 'bottom-right',
  className,
}: FABProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const hasMultipleActions = actions && actions.length > 0;

  const handleClick = () => {
    if (hasMultipleActions) {
      setIsExpanded(!isExpanded);
    } else if (onClick) {
      onClick();
    }
  };

  return (
    <div className={cn('fixed z-50', positionClasses[position], className)}>
      {/* Action buttons */}
      <AnimatePresence>
        {isExpanded && hasMultipleActions && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute bottom-16 right-0 flex flex-col items-end gap-3 mb-2"
          >
            {actions.map((action, index) => (
              <motion.button
                key={index}
                initial={{ opacity: 0, y: 20, scale: 0.8 }}
                animate={{
                  opacity: 1,
                  y: 0,
                  scale: 1,
                  transition: { delay: index * 0.05 },
                }}
                exit={{
                  opacity: 0,
                  y: 20,
                  scale: 0.8,
                  transition: { delay: (actions.length - index - 1) * 0.05 },
                }}
                onClick={() => {
                  action.onClick();
                  setIsExpanded(false);
                }}
                className={cn(
                  'flex items-center gap-3 px-4 py-3',
                  'bg-glass-bg backdrop-blur-xl',
                  'border border-glass-border rounded-2xl',
                  'shadow-glass-hover',
                  'text-foreground-secondary hover:text-accent',
                  'transition-colors duration-200'
                )}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <span className="text-sm font-medium whitespace-nowrap">{action.label}</span>
                <span className="flex items-center justify-center w-10 h-10 rounded-xl bg-accent/10 text-accent">
                  {action.icon}
                </span>
              </motion.button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main FAB button */}
      <motion.button
        onClick={handleClick}
        className={cn(
          'flex items-center justify-center',
          'bg-gradient-primary text-white',
          'shadow-lg shadow-accent/30',
          'focus:outline-none focus:ring-2 focus:ring-accent/50 focus:ring-offset-2 focus:ring-offset-background',
          label ? 'px-5 py-3 gap-2 rounded-2xl' : 'w-14 h-14 rounded-full'
        )}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        animate={{ rotate: hasMultipleActions && isExpanded ? 45 : 0 }}
        transition={{ type: 'spring', stiffness: 300, damping: 20 }}
        aria-label={label || 'Actions'}
        aria-expanded={isExpanded}
      >
        {hasMultipleActions ? (
          isExpanded ? <X size={24} /> : <Plus size={24} />
        ) : (
          icon || <Plus size={24} />
        )}
        {label && <span className="font-semibold">{label}</span>}
      </motion.button>

      {/* Backdrop for closing expanded FAB */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 -z-10"
            onClick={() => setIsExpanded(false)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

export default FAB;
