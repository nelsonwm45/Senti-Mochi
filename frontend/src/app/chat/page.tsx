'use client';

import { useEffect, useRef, useState } from 'react';
import AgenticThought from '@/components/chat/AgenticThought';
import MessageBubble from '@/components/chat/MessageBubble';
import ChatInput from '@/components/chat/ChatInput';
import CitationPanel from '@/components/chat/CitationPanel';
import { useChat } from '@/hooks/useChat';
import { MessageCircle, FileText, Trash2 } from 'lucide-react';

import ProtectedLayout from '@/components/layouts/ProtectedLayout';

export default function ChatPage() {
  const { messages, agentState, isLoading, currentCitations, sendMessage, clearMessages } = useChat();
  const [citationPanelOpen, setCitationPanelOpen] = useState(false);
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
    console.log('Citation clicked:', citationNumber);
    // TODO: Implement document viewer navigation
  };

  return (
    <ProtectedLayout>
      <div className="h-full flex flex-col bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
        {/* Header */}
        <div className="flex-shrink-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
          <div className="max-w-4xl mx-auto flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl">
                <MessageCircle className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                  AI Chat Assistant
                </h1>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Ask questions about your financial documents
                </p>
              </div>
            </div>

            {messages.length > 0 && (
              <button
                onClick={clearMessages}
                className="p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                title="Clear chat"
              >
                <Trash2 className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="flex-1 overflow-hidden flex relative">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto">
            <div className="max-w-4xl mx-auto px-6 py-8">
              {/* Agentic Thought Visualization */}
              <AgenticThought state={agentState} />

              {/* Messages */}
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <div className="p-6 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full mb-6">
                    <MessageCircle className="w-16 h-16 text-white" />
                  </div>
                  <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-3">
                    Start a Conversation
                  </h2>
                  <p className="text-gray-600 dark:text-gray-400 max-w-md mb-6">
                    Ask me anything about your financial documents. I'll search through them and provide accurate answers with citations.
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl">
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
                        className="px-4 py-3 text-left bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-500 dark:hover:border-blue-600 transition-colors disabled:opacity-50"
                      >
                        <div className="flex items-center space-x-2">
                          <FileText className="w-4 h-4 text-blue-500 flex-shrink-0" />
                          <span className="text-sm text-gray-700 dark:text-gray-300">
                            {suggestion}
                          </span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {messages.map((message, index) => (
                    <MessageBubble
                      key={index}
                      role={message.role}
                      content={message.content}
                      timestamp={message.timestamp}
                      citations={message.citations?.map(c => c.sourceNumber)}
                      onCitationClick={(num) => {
                        handleCitationClick(num);
                        setCitationPanelOpen(true);
                      }}
                    />
                  ))}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>
          </div>

          {/* Citation Panel */}
          <CitationPanel
            citations={currentCitations}
            isOpen={citationPanelOpen}
            onClose={() => setCitationPanelOpen(false)}
            onCitationClick={(citation) => {
              console.log('Navigate to:', citation);
              // TODO: Implement document viewer
            }}
          />
        </div>

        {/* Input Area */}
        <ChatInput
          onSend={handleSend}
          disabled={isLoading}
          placeholder={
            isLoading
              ? 'Please wait...'
              : 'Ask a question about your documents...'
          }
        />
      </div>
    </ProtectedLayout>
  );
}
