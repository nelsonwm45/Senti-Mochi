'use client';

import { motion } from 'framer-motion';
import { Plus, MessageSquare, Menu, Trash2 } from 'lucide-react';
import { GlassButton } from '@/components/ui/GlassButton';
import { cn } from '@/lib/utils';
import { useEffect, useState } from 'react';
import { ChatSession } from '@/hooks/useChat';

interface ChatSidebarProps {
  onNewChat: () => void;
  isOpen: boolean;
  onClose: () => void;
  sessions: ChatSession[];
  currentSessionId: string | null;
  onSelectSession: (session: ChatSession) => void;
  onDeleteSession: (sessionId: string) => void;
}

export default function ChatSidebar({
  onNewChat,
  isOpen,
  onClose,
  sessions,
  currentSessionId,
  onSelectSession,
  onDeleteSession,
}: ChatSidebarProps) {
  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-30 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar Container */}
      <motion.div
        className={cn(
          "fixed lg:static top-0 left-0 z-40 h-full w-80 bg-glass-bg border-r border-glass-border flex flex-col transition-transform duration-300 ease-in-out lg:translate-x-0 backdrop-blur-xl",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Header */}
        <div className="p-6 border-b border-glass-border">
          <GlassButton 
            className="w-full justify-center gap-2"
            onClick={() => {
              onNewChat();
              if (window.innerWidth < 1024) onClose();
            }}
            leftIcon={<Plus size={20} />}
          >
            New Chat
          </GlassButton>
        </div>

        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          <div className="text-xs font-semibold text-foreground-muted uppercase tracking-wider px-4 py-2">
            Recent Conversations
          </div>
          
          {sessions.length === 0 ? (
            <div className="text-sm text-foreground-muted px-4 py-2 italic text-center">
              No recent conversations
            </div>
          ) : (
            sessions.map((session) => (
              <button
                key={session.id}
                onClick={() => {
                    onSelectSession(session);
                    if (window.innerWidth < 1024) onClose();
                }}
                className={cn(
                  "w-full text-left p-3 rounded-xl transition-colors group relative", // Added relative
                  currentSessionId === session.id 
                    ? "bg-accent/10 border border-accent/20" 
                    : "hover:bg-white/5 active:bg-white/10"
                )}
              >
                <div className="flex items-center gap-3 pr-8"> {/* Added padding for delete button */}
                  <MessageSquare className={cn(
                    "w-4 h-4 transition-colors flex-shrink-0",
                    currentSessionId === session.id ? "text-accent" : "text-foreground-muted group-hover:text-accent"
                  )} />
                  <div className="flex-1 min-w-0">
                    <p className={cn(
                      "text-sm font-medium truncate transition-colors",
                      currentSessionId === session.id ? "text-foreground" : "text-foreground group-hover:text-accent"
                    )}>
                      {session.title}
                    </p>
                    <p className="text-xs text-foreground-muted truncate">
                      {session.date}
                    </p>
                  </div>
                </div>
                
                {/* Delete Button */}
                <div 
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg text-foreground-muted hover:text-red-500 hover:bg-red-500/10 opacity-0 group-hover:opacity-100 transition-all cursor-pointer"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (confirm('Delete this chat?')) {
                        onDeleteSession(session.id);
                    }
                  }}
                  title="Delete chat"
                >
                  <Trash2 size={14} />
                </div>
              </button>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-glass-border">
          <div className="text-xs text-center text-foreground-muted">
            Mochi AI Chat v1.0
          </div>
        </div>
      </motion.div>
    </>
  );
}
