'use client';

import { useEffect, useRef, useState } from 'react';
import { Menu, MessageSquare, Trash2 } from 'lucide-react';
import AgenticThought from '@/components/chat/AgenticThought';
import MessageBubble from '@/components/chat/MessageBubble';
import ChatInput from '@/components/chat/ChatInput';
import CitationPanel from '@/components/chat/CitationPanel';
import ChatSidebar from '@/components/chat/ChatSidebar';
import { useChat } from '@/hooks/useChat';
import { GlassButton } from '@/components/ui/GlassButton';
import { chatApi } from '@/lib/api/chat';
import ProtectedLayout from '@/components/layouts/ProtectedLayout';

export default function ChatPage() {
  const { messages, agentState, isLoading, currentCitations, sendMessage, clearMessages } = useChat();
  const [citationPanelOpen, setCitationPanelOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeCitationId, setActiveCitationId] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Open citation panel when citations are available
  useEffect(() => {
    if (currentCitations.length > 0) {
      setCitationPanelOpen(true);
    }
  }, [currentCitations]);

  const handleSend = (content: string) => {
    sendMessage(content, false); // Set to true for streaming
  };

  const handleCitationClick = (citationNumber: number) => {
    setActiveCitationId(citationNumber);
    setCitationPanelOpen(true);
  };

  const handleFeedback = async (messageId: string, rating: number) => {
    try {
      await chatApi.feedback(messageId, rating);
      console.log('Feedback submitted:', messageId, rating);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
  };

  return (
    <ProtectedLayout>
      <div className="h-[calc(100vh-theme(spacing.20))] flex overflow-hidden rounded-2xl border border-glass-border bg-glass-bg shadow-2xl relative">
        {/* Background Gradients */}
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10 pointer-events-none">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-accent/5 rounded-full blur-3xl" />
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl" />
        </div>

        {/* Sidebar */}
        <ChatSidebar 
          onNewChat={clearMessages}
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
        />

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col min-w-0 bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm relative">
          
          {/* Header */}
          <div className="flex-shrink-0 px-6 py-4 border-b border-glass-border flex items-center justify-between bg-glass-bg backdrop-blur-xl">
            <div className="flex items-center gap-3">
              <button 
                className="lg:hidden p-2 -ml-2 hover:bg-white/10 rounded-lg transition-colors"
                onClick={() => setSidebarOpen(true)}
              >
                <Menu size={20} />
              </button>
              <div className="flex flex-col">
                <h1 className="text-lg font-semibold text-foreground flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                  Mochi Assistant
                </h1>
                <p className="text-xs text-foreground-muted">Use natural language to query your docs</p>
              </div>
            </div>

            {messages.length > 0 && (
              <GlassButton
                variant="ghost"
                size="sm"
                onClick={clearMessages}
                className="text-red-500 hover:text-red-600 hover:bg-red-500/10"
                leftIcon={<Trash2 size={16} />}
              >
                Clear
              </GlassButton>
            )}
          </div>

          {/* Messages Scroll Area */}
          <div className="flex-1 overflow-y-auto custom-scrollbar relative">
            <div className="max-w-4xl mx-auto px-6 py-8">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <div className="w-20 h-20 bg-gradient-brand rounded-3xl flex items-center justify-center mb-6 shadow-lg shadow-accent/20">
                    <MessageSquare className="w-10 h-10 text-white" />
                  </div>
                  <h2 className="text-2xl font-bold text-foreground mb-3">
                    Start a Conversation
                  </h2>
                  <p className="text-foreground-muted max-w-md mb-8">
                    I can help you analyze documents, summarize reports, and answer questions about your financial data.
                  </p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-2xl">
                    {[
                      'What was the Q1 Revenue?',
                      'Summarize the risk assessment',
                      'What are the key highlights?',
                      'Show me account balances',
                    ].map((suggestion, index) => (
                      <button
                        key={index}
                        onClick={() => handleSend(suggestion)}
                        disabled={isLoading}
                        className="text-left p-4 rounded-xl border border-glass-border bg-glass-bg hover:bg-white/5 hover:border-accent/30 hover:shadow-lg transition-all duration-300 group"
                      >
                        <span className="text-sm font-medium text-foreground group-hover:text-accent transition-colors">
                          {suggestion}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="space-y-6 pb-4">
                  {messages.map((message, index) => (
                    <MessageBubble
                      key={index}
                      id={message.id}
                      role={message.role}
                      content={message.content}
                      timestamp={message.timestamp}
                      citations={message.citations?.map(c => c.sourceNumber)}
                      onCitationClick={handleCitationClick}
                      onFeedback={handleFeedback}
                    />
                  ))}
                  
                  <AgenticThought state={agentState} />
                  
                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>
          </div>

          {/* Input Area */}
          <ChatInput
            onSend={handleSend}
            disabled={isLoading}
            placeholder={
              isLoading
                ? 'Processing your request...'
                : 'Ask a question about your documents...'
            }
          />
        </div>

        {/* Citation Panel */}
        <CitationPanel
          citations={currentCitations}
          isOpen={citationPanelOpen}
          onClose={() => {
              setCitationPanelOpen(false);
              setActiveCitationId(null);
          }}
          activeCitationId={activeCitationId}
        />
      </div>
    </ProtectedLayout>
  );
}
