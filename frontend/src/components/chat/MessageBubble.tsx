'use client';

import { motion } from 'framer-motion';
import { User, Copy, Check } from 'lucide-react';
import Image from 'next/image';
import { useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { GlassCard } from '@/components/ui/GlassCard';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MessageBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  citations?: number[];
  onCitationClick?: (citationNumber: number) => void;
  mochiVariant?: 'green' | 'red' | 'purple';
  userAvatarUrl?: string; // New prop for user avatar
}

export default function MessageBubble({
  role,
  content,
  timestamp,
  citations = [],
  onCitationClick,
  mochiVariant = 'green',
  userAvatarUrl, 
}: MessageBubbleProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isUser = role === 'user';

  // Pre-process content to convert citation markers [Source N] into links we can intercept
  // [Source 1] -> [Source 1](#citation-1)
  // We use a hash fragment (#citation-1) because custom protocols like citation:// get sanitized by ReactMarkdown
  const processedContent = content.replace(
    /\[Source (\d+)(?:[^\]]*)\]/g,
    '[Source $1](#citation-$1)'
  );

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
            : 'bg-transparent overflow-hidden'
        }`}>
          {isUser ? (
            userAvatarUrl ? (
              <div className="relative w-full h-full overflow-hidden rounded-xl">
                 <img 
                    src={userAvatarUrl} 
                    alt="User" 
                    className="w-full h-full object-cover"
                  />
              </div>
            ) : (
              <User className="w-5 h-5 text-white" />
            )
          ) : (
            <div className="relative w-full h-full">
              <Image 
                src={
                  mochiVariant === 'red' ? '/MochiRed.png' :
                  mochiVariant === 'purple' ? '/MochiPurple.png' :
                  '/MochiGreen.png'
                }
                alt="Mochi Avatar" 
                fill
                className="object-cover"
              />
            </div>
          )}
        </div>

        {/* Message Content */}
        <div className={`flex-1 ${isUser ? 'text-right' : 'text-left'}`}>
          {isUser ? (
            <div className="inline-block px-5 py-4 rounded-2xl rounded-tr-sm bg-gradient-brand text-white shadow-lg shadow-accent/20">
              <div className="text-sm leading-relaxed text-left">
                <p className="whitespace-pre-wrap">{content}</p>
              </div>
            </div>
          ) : (
            <GlassCard className="rounded-tl-sm px-5 py-4 bg-white/40 dark:bg-gray-900/40">
              <div className="text-sm leading-relaxed text-foreground markdown-content prose prose-sm dark:prose-invert max-w-none break-words">
                <ReactMarkdown 
                  remarkPlugins={[remarkGfm]}
                  components={{
                    // Override anchor tags to handle citations
                    a: ({ href, children, ...props }) => {
                      // Check for citation hash
                      if (href?.startsWith('#citation-')) {
                        const citationNum = parseInt(href.replace('#citation-', ''));
                        return (
                          <button
                            onClick={(e) => {
                              e.preventDefault();
                              onCitationClick?.(citationNum);
                            }}
                            className="inline-flex items-center px-2 py-0.5 mx-0.5 text-[10px] font-bold uppercase tracking-wider rounded-full bg-accent/10 text-accent hover:bg-accent/20 transition-colors border border-accent/20 font-mono no-underline transform hover:scale-105"
                            title={`View Source ${citationNum}`}
                          >
                            {children}
                          </button>
                        );
                      }
                      return (
                        <a 
                          href={href} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className="text-accent hover:underline"
                          {...props}
                        >
                          {children}
                        </a>
                      );
                    },
                    // Enhance table styling
                    table: ({ children }) => (
                      <div className="overflow-x-auto my-4 rounded-lg border border-glass-border">
                        <table className="min-w-full divide-y divide-glass-border bg-white/5">
                          {children}
                        </table>
                      </div>
                    ),
                    thead: ({ children }) => (
                      <thead className="bg-white/10">
                        {children}
                      </thead>
                    ),
                    th: ({ children }) => (
                      <th className="px-3 py-2 text-left text-xs font-semibold text-foreground uppercase tracking-wider">
                        {children}
                      </th>
                    ),
                    td: ({ children }) => (
                      <td className="px-3 py-2 text-sm text-foreground/80 whitespace-nowrap border-t border-glass-border/50">
                          {children}
                      </td>
                    ),
                    // Enhance code blocks
                    pre: ({ children }) => (
                      <pre className="bg-gray-900/90 text-gray-100 p-3 rounded-lg overflow-x-auto my-2 border border-white/10">
                        {children}
                      </pre>
                    ),
                    code: ({ children, className }) => {
                       const isInline = !className; // Basic heuristic
                       if (isInline) {
                           return <code className="bg-accent/10 text-accent px-1 py-0.5 rounded text-xs font-mono">{children}</code>;
                       }
                       return <code className={className}>{children}</code>;
                    }
                  }}
                >
                  {processedContent}
                </ReactMarkdown>
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
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
