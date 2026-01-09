'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Search, Brain, Sparkles, CheckCircle, Loader2 } from 'lucide-react';

export type AgentState = 'idle' | 'searching' | 'analyzing' | 'generating' | 'complete';

interface AgenticThoughtProps {
  state: AgentState;
  message?: string;
}

interface StateConfigItem {
  icon: any;
  label: string;
  color: string;
  bgGradient: string;
  message: string;
  animate?: boolean;
}

const STATE_CONFIG: Record<AgentState, StateConfigItem> = {
  idle: {
    icon: Sparkles,
    label: 'Ready',
    color: 'text-gray-400',
    bgGradient: 'from-gray-400 to-gray-500',
    message: 'Ready',
  },
  searching: {
    icon: Search,
    label: 'Searching',
    color: 'text-blue-500',
    bgGradient: 'from-blue-500 to-cyan-500',
    message: 'Searching...',
    animate: true,
  },
  analyzing: {
    icon: Brain,
    label: 'Analyzing',
    color: 'text-purple-500',
    bgGradient: 'from-purple-500 to-pink-500',
    message: 'Thinking...',
    animate: true,
  },
  generating: {
    icon: Sparkles,
    label: 'Generating',
    color: 'text-emerald-500',
    bgGradient: 'from-emerald-500 to-teal-500',
    message: 'Writing...',
    animate: true,
  },
  complete: {
    icon: CheckCircle,
    label: 'Done',
    color: 'text-green-500',
    bgGradient: 'from-green-500 to-emerald-600',
    message: 'Complete',
  },
};

export default function AgenticThought({ state, message }: AgenticThoughtProps) {
  const config = STATE_CONFIG[state];
  const Icon = config.icon;

  return (
    <AnimatePresence mode="wait">
      {state !== 'idle' && (
        <motion.div
          key={state}
          initial={{ opacity: 0, y: 10, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -10, scale: 0.9 }}
          transition={{ duration: 0.2 }}
          className="flex justify-center mb-6"
        >
          <div className="relative group">
            {/* Glow Effect */}
            <div className={`absolute -inset-0.5 bg-gradient-to-r ${config.bgGradient} rounded-full opacity-30 blur group-hover:opacity-50 transition duration-1000 group-hover:duration-200 animate-tilt`}></div>
            
            {/* Pill Container */}
            <div className="relative flex items-center bg-white dark:bg-gray-800 rounded-full px-4 py-2 ring-1 ring-gray-900/5 dark:ring-white/10 shadow-sm leading-none">
              
              {/* Icon */}
              <div className="flex-shrink-0 mr-3">
                 {config.animate && state === 'searching' ? (
                    <Loader2 className={`w-4 h-4 ${config.color} animate-spin`} />
                  ) : (
                    <Icon className={`w-4 h-4 ${config.color}`} />
                  )}
              </div>

              {/* Text */}
              <div className="flex items-center space-x-2">
                <span className={`text-sm font-medium text-gray-900 dark:text-gray-100`}>
                  {config.label}
                </span>
                
                {/* Separator */}
                <span className="text-gray-300 dark:text-gray-600">|</span>
                
                <span className="text-xs text-gray-500 dark:text-gray-400 truncate max-w-[200px]">
                  {message || config.message}
                </span>
              </div>

              {/* Pulsing Dot */}
              {config.animate && (
                 <span className="flex h-2 w-2 ml-3 relative">
                    <span className={`animate-ping absolute inline-flex h-full w-full rounded-full bg-gradient-to-r ${config.bgGradient} opacity-75`}></span>
                    <span className={`relative inline-flex rounded-full h-2 w-2 bg-gradient-to-r ${config.bgGradient}`}></span>
                  </span>
              )}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
