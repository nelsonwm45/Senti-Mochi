'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Brain, Sparkles, CheckCircle, Loader2 } from 'lucide-react';

export type AgentState = 'idle' | 'searching' | 'analyzing' | 'generating' | 'complete';

interface AgenticThoughtProps {
  state: AgentState;
  message?: string;
}

const STATE_CONFIG = {
  idle: {
    icon: Sparkles,
    label: 'Ready',
    color: 'text-gray-400',
    bgGradient: 'from-gray-400 to-gray-500',
    message: 'Ask me anything about your documents',
  },
  searching: {
    icon: Search,
    label: 'Searching',
    color: 'text-blue-500',
    bgGradient: 'from-blue-500 to-cyan-500',
    message: 'Searching through your documents...',
    animate: true,
  },
  analyzing: {
    icon: Brain,
    label: 'Analyzing',
    color: 'text-purple-500',
    bgGradient: 'from-purple-500 to-pink-500',
    message: 'Analyzing context and relevance...',
    animate: true,
  },
  generating: {
    icon: Sparkles,
    label: 'Generating',
    color: 'text-emerald-500',
    bgGradient: 'from-emerald-500 to-teal-500',
    message: 'Crafting your answer...',
    animate: true,
  },
  complete: {
    icon: CheckCircle,
    label: 'Complete',
    color: 'text-green-500',
    bgGradient: 'from-green-500 to-emerald-600',
    message: 'Response ready!',
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
          initial={{ opacity: 0, y: -20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -20, scale: 0.95 }}
          transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
          className="mb-6"
        >
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 p-6 overflow-hidden relative">
            {/* Animated background gradient */}
            <motion.div
              className={`absolute inset-0 bg-gradient-to-r ${config.bgGradient} opacity-5`}
              animate={config.animate ? {
                x: ['-100%', '100%'],
              } : {}}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'linear',
              }}
            />

            <div className="relative flex items-center space-x-4">
              {/* Animated Icon */}
              <motion.div
                className={`flex-shrink-0 relative`}
                animate={config.animate ? {
                  scale: [1, 1.1, 1],
                  rotate: state === 'analyzing' ? [0, 5, -5, 0] : 0,
                } : {}}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }}
              >
                <div className={`p-4 bg-gradient-to-br ${config.bgGradient} rounded-xl shadow-lg`}>
                  {config.animate && state === 'searching' ? (
                    <Loader2 className="w-8 h-8 text-white animate-spin" />
                  ) : (
                    <Icon className="w-8 h-8 text-white" />
                  )}
                </div>
                
                {/* Pulse effect */}
                {config.animate && (
                  <motion.div
                    className={`absolute inset-0 bg-gradient-to-br ${config.bgGradient} rounded-xl`}
                    animate={{
                      scale: [1, 1.3, 1],
                      opacity: [0.5, 0, 0.5],
                    }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      ease: 'easeOut',
                    }}
                  />
                )}
              </motion.div>

              {/* Text Content */}
              <div className="flex-1 min-w-0">
                <motion.div
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 }}
                >
                  <div className="flex items-center space-x-2 mb-1">
                    <h3 className={`text-lg font-semibold ${config.color}`}>
                      {config.label}
                    </h3>
                    {config.animate && (
                      <div className="flex space-x-1">
                        {[0, 1, 2].map((i) => (
                          <motion.div
                            key={i}
                            className={`w-1.5 h-1.5 rounded-full ${config.color}`}
                            animate={{
                              opacity: [0.3, 1, 0.3],
                              scale: [0.8, 1, 0.8],
                            }}
                            transition={{
                              duration: 1,
                              repeat: Infinity,
                              delay: i * 0.15,
                            }}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {message || config.message}
                  </p>
                </motion.div>
              </div>
            </div>

            {/* Progress bar for active states */}
            {config.animate && (
              <motion.div
                className="mt-4 h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
              >
                <motion.div
                  className={`h-full bg-gradient-to-r ${config.bgGradient} rounded-full`}
                  initial={{ width: '0%' }}
                  animate={{ width: '100%' }}
                  transition={{
                    duration: 3,
                    ease: 'easeInOut',
                  }}
                />
              </motion.div>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
