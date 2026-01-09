'use client';

import { motion } from 'framer-motion';
import { User, Bot, Copy, Check } from 'lucide-react';
import { useState } from 'react';
import { formatDistanceToNow } from 'date-fns';

interface MessageBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  citations?: number[];
  onCitationClick?: (citationNumber: number) => void;
}

export default function MessageBubble({
  role,
  content,
  timestamp,
  citations = [],
  onCitationClick,
}: MessageBubbleProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Process content to make citations clickable
  const renderContent = () => {
    if (role === 'user' || citations.length === 0) {
      return <p className="whitespace-pre-wrap">{content}</p>;
    }

    // Replace [Source N: ...] with clickable badges
    const parts = content.split(/(\[Source \d+(?:[^\]]*)\])/g);
    
    return (
      <p className="whitespace-pre-wrap">
        {parts.map((part, index) => {
          const match = part.match(/\[Source (\d+)(?:[^\]]*)\]/);
          if (match) {
            const citationNum = parseInt(match[1]);
            return (
              <button
                key={index}
                onClick={() => onCitationClick?.(citationNum)}
                className="inline-flex items-center px-2 py-0.5 mx-0.5 text-[10px] font-bold uppercase tracking-wider rounded-full bg-indigo-100 dark:bg-indigo-500/20 text-indigo-600 dark:text-indigo-300 hover:bg-indigo-200 dark:hover:bg-indigo-500/30 transition-colors border border-indigo-200 dark:border-indigo-500/30 font-mono"
                title={part} // Show full citation on hover
              >
                Source {match[1]}
              </button>
            );
          }
          return <span key={index}>{part}</span>;
        })}
      </p>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex ${role === 'user' ? 'justify-end' : 'justify-start'} mb-6`}
    >
      <div className={`flex ${role === 'user' ? 'flex-row-reverse' : 'flex-row'} max-w-3xl space-x-3 ${role === 'user' ? 'space-x-reverse' : ''}`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
          role === 'user'
            ? 'bg-gradient-to-br from-blue-500 to-purple-600'
            : 'bg-gradient-to-br from-emerald-500 to-teal-600'
        }`}>
          {role === 'user' ? (
            <User className="w-5 h-5 text-white" />
          ) : (
            <Bot className="w-5 h-5 text-white" />
          )}
        </div>

        {/* Message Content */}
        <div className={`flex-1 ${role === 'user' ? 'text-right' : 'text-left'}`}>
          <div className={`inline-block px-4 py-3 rounded-2xl ${
            role === 'user'
              ? 'bg-gradient-to-br from-blue-500 to-purple-600 text-white'
              : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700'
          }`}>
            <div className="text-sm leading-relaxed">
              {renderContent()}
            </div>
          </div>

          {/* Footer with timestamp and actions */}
          <div className={`flex items-center mt-2 space-x-2 text-xs text-gray-500 dark:text-gray-400 ${
            role === 'user' ? 'justify-end' : 'justify-start'
          }`}>
            {timestamp && (
              <span>
                {formatDistanceToNow(new Date(timestamp), { addSuffix: true })}
              </span>
            )}
            
            {role === 'assistant' && (
              <button
                onClick={handleCopy}
                className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
                title="Copy message"
              >
                {copied ? (
                  <Check className="w-4 h-4 text-green-500" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
