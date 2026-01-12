'use client';

import { motion } from 'framer-motion';
import { User, Bot, Copy, Check, ThumbsUp, ThumbsDown } from 'lucide-react';
import { useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { GlassCard } from '@/components/ui/GlassCard';

interface MessageBubbleProps {
  id?: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  citations?: number[];
  onCitationClick?: (citationNumber: number) => void;
  onFeedback?: (messageId: string, rating: number) => void;
}

export default function MessageBubble({
  id,
  role,
  content,
  timestamp,
  citations = [],
  onCitationClick,
  onFeedback,
}: MessageBubbleProps) {
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<number | null>(null);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleFeedback = (rating: number) => {
    if (feedback === rating) return; // Prevent duplicate
    setFeedback(rating);
    if (id && onFeedback) {
      onFeedback(id, rating);
    }
  };

  // ... (renderContent code remains same)
  // Process content to make citations clickable
  const renderContent = () => {
    // ... (same as before)
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
                className="inline-flex items-center px-2 py-0.5 mx-0.5 text-[10px] font-bold uppercase tracking-wider rounded-full bg-accent/10 text-accent hover:bg-accent/20 transition-colors border border-accent/20 font-mono"
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

  const isUser = role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6`}
    >
      <div className={`flex ${isUser ? 'flex-row-reverse' : 'flex-row'} max-w-3xl gap-4`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center shadow-lg ${
          isUser
            ? 'bg-gradient-brand'
            : 'bg-glass-bg border border-glass-border backdrop-blur-md'
        }`}>
          {isUser ? (
            <User className="w-5 h-5 text-white" />
          ) : (
            <Bot className="w-5 h-5 text-accent" />
          )}
        </div>

        {/* Message Content */}
        <div className={`flex-1 ${isUser ? 'text-right' : 'text-left'}`}>
          {isUser ? (
            <div className="inline-block px-5 py-4 rounded-2xl rounded-tr-sm bg-gradient-brand text-white shadow-lg shadow-accent/20">
              <div className="text-sm leading-relaxed text-left">
                {renderContent()}
              </div>
            </div>
          ) : (
            <GlassCard className="rounded-tl-sm px-5 py-4">
              <div className="text-sm leading-relaxed text-foreground">
                {renderContent()}
              </div>
            </GlassCard>
          )}

          {/* Footer with timestamp and actions */}
          <div className={`flex items-center mt-2 gap-2 text-xs text-foreground-muted ${
            isUser ? 'justify-end' : 'justify-start'
          }`}>
            {timestamp && (
              <span>
                {formatDistanceToNow(new Date(timestamp), { addSuffix: true })}
              </span>
            )}
            
            {!isUser && (
              <>
                <button
                  onClick={handleCopy}
                  className="p-1.5 hover:bg-white/10 rounded-lg transition-colors ml-1"
                  title="Copy message"
                >
                  {copied ? (
                    <Check className="w-3.5 h-3.5 text-green-500" />
                  ) : (
                    <Copy className="w-3.5 h-3.5" />
                  )}
                </button>
                <div className="flex items-center gap-1 border-l border-white/10 pl-2 ml-1">
                   <button
                     onClick={() => handleFeedback(1)}
                     className={`p-1.5 rounded-lg transition-colors ${feedback === 1 ? 'text-green-500 bg-green-500/10' : 'hover:bg-white/10'}`}
                   >
                     <ThumbsUp className="w-3.5 h-3.5" />
                   </button>
                   <button
                     onClick={() => handleFeedback(-1)}
                     className={`p-1.5 rounded-lg transition-colors ${feedback === -1 ? 'text-red-500 bg-red-500/10' : 'hover:bg-white/10'}`}
                   >
                     <ThumbsDown className="w-3.5 h-3.5" />
                   </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
