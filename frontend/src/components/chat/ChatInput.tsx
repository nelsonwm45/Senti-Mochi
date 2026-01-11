'use client';

import { useState, KeyboardEvent } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { GlassCard } from '@/components/ui/GlassCard';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function ChatInput({
  onSend,
  disabled = false,
  placeholder = 'Ask a question about your documents...',
}: ChatInputProps) {
  const [message, setMessage] = useState('');

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSend(message.trim());
      setMessage('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="p-2 md:p-4 bg-transparent w-full">
      <div className="max-w-3xl mx-auto">
        <GlassCard className="relative !p-1 flex !flex-row items-center !gap-2 overflow-visible min-h-[50px]">
          {/* Input */}
          <div className="flex-1 relative flex items-center">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={disabled}
              placeholder={placeholder}
              rows={1}
              className="w-full px-4 py-2 bg-transparent text-foreground placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none resize-none disabled:opacity-50 disabled:cursor-not-allowed max-h-[150px] text-sm md:text-base leading-relaxed"
              style={{
                minHeight: '40px',
              }}
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement;
                target.style.height = 'auto';
                target.style.height = `${target.scrollHeight}px`;
                // If height > 40px, align parent to items-end to allow expansion upward/downward without jumping
                if (target.scrollHeight > 44) {
                     target.parentElement?.parentElement?.classList.replace('items-center', 'items-end');
                     target.parentElement?.parentElement?.classList.add('pb-2');
                } else {
                     target.parentElement?.parentElement?.classList.replace('items-end', 'items-center');
                     target.parentElement?.parentElement?.classList.remove('pb-2');
                }
              }}
            />
          </div>

          {/* Send Button */}
          <button
            onClick={handleSend}
            disabled={disabled || !message.trim()}
            className={`
              flex-shrink-0 p-2.5 rounded-xl transition-all duration-300
              ${disabled || !message.trim()
                ? 'bg-glass-border cursor-not-allowed opacity-50'
                : 'bg-gradient-brand text-white shadow-lg shadow-accent/25 hover:shadow-accent/40 hover:scale-105 active:scale-95'
              }
            `}
          >
            {disabled ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </GlassCard>

        {/* Hints */}
        <div className="mt-2 text-[10px] md:text-xs text-foreground-muted text-center flex items-center justify-center gap-4 opacity-70">
          <span>
            <kbd className="px-1.5 py-0.5 bg-glass-bg border border-glass-border rounded-md mr-1.5 font-sans font-medium">Enter</kbd>
            to send
          </span>
          <span>
            <kbd className="px-1.5 py-0.5 bg-glass-bg border border-glass-border rounded-md mr-1.5 font-sans font-medium">Shift + Enter</kbd>
            for new line
          </span>
        </div>
      </div>
    </div>
  );
}
