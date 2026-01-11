'use client';

import { motion } from 'framer-motion';
import { Plus, MessageSquare, Menu } from 'lucide-react';
import { GlassButton } from '@/components/ui/GlassButton';
import { cn } from '@/lib/utils';
import { useEffect, useState } from 'react';

interface ChatSidebarProps {
  onNewChat: () => void;
  isOpen: boolean;
  onClose: () => void;
}

export default function ChatSidebar({
  onNewChat,
  isOpen,
  onClose,
}: ChatSidebarProps) {
  // Mock conversations for now
  const [conversations, setConversations] = useState([
    { id: 1, title: 'Q1 Financial Report Analysis', date: '2 hours ago' },
    { id: 2, title: 'Risk Assessment Summary', date: 'Yesterday' },
    { id: 3, title: 'Account Balances Inquiry', date: '2 days ago' },
  ]);

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
          
          {conversations.map((chat) => (
            <button
              key={chat.id}
              className="w-full text-left p-3 rounded-xl hover:bg-white/5 active:bg-white/10 transition-colors group"
            >
              <div className="flex items-center gap-3">
                <MessageSquare className="w-4 h-4 text-foreground-muted group-hover:text-accent transition-colors" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground truncate group-hover:text-accent transition-colors">
                    {chat.title}
                  </p>
                  <p className="text-xs text-foreground-muted truncate">
                    {chat.date}
                  </p>
                </div>
              </div>
            </button>
          ))}
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
