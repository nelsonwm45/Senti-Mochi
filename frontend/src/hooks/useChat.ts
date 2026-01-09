'use client';

import { useState } from 'react';
import { chatApi, QueryResponse, CitationInfo } from '@/lib/api/chat';
import { AgentState } from '@/components/chat/AgenticThought';

interface ChatMessage {
	role: 'user' | 'assistant';
	content: string;
	timestamp: string;
	citations?: CitationInfo[];
}

export function useChat() {
	const [messages, setMessages] = useState<ChatMessage[]>([]);
	const [agentState, setAgentState] = useState<AgentState>('idle');
	const [isLoading, setIsLoading] = useState(false);
	const [currentCitations, setCurrentCitations] = useState<CitationInfo[]>([]);

	const sendMessage = async (content: string, stream = true) => {
		// Add user message
		const userMessage: ChatMessage = {
			role: 'user',
			content,
			timestamp: new Date().toISOString(),
		};
		setMessages((prev) => [...prev, userMessage]);
		setIsLoading(true);

		try {
			if (stream) {
				await handleStreamingResponse(content);
			} else {
				await handleNonStreamingResponse(content);
			}
		} catch (error) {
			console.error('Chat error:', error);
			const errorMessage: ChatMessage = {
				role: 'assistant',
				content: error instanceof Error && error.message.includes('No relevant information')
					? 'I couldn\'t find relevant information in your documents to answer this question.'
					: 'Sorry, I encountered an error processing your request.',
				timestamp: new Date().toISOString(),
			};
			setMessages((prev) => [...prev, errorMessage]);
			setAgentState('complete');
		} finally {
			setIsLoading(false);
		}
	};

	const handleStreamingResponse = async (query: string) => {
		setAgentState('searching');
		await new Promise(resolve => setTimeout(resolve, 500));

		setAgentState('analyzing');
		await new Promise(resolve => setTimeout(resolve, 800));

		setAgentState('generating');

		let accumulatedContent = '';
		const assistantMessage: ChatMessage = {
			role: 'assistant',
			content: '',
			timestamp: new Date().toISOString(),
		};

		setMessages((prev) => [...prev, assistantMessage]);

		try {
			const stream = chatApi.queryStream({ query, stream: true });

			for await (const chunk of stream) {
				accumulatedContent += chunk;
				setMessages((prev) => {
					const newMessages = [...prev];
					newMessages[newMessages.length - 1] = {
						...assistantMessage,
						content: accumulatedContent,
					};
					return newMessages;
				});
			}
		} catch (error) {
			console.error('Streaming error:', error);
		}

		setAgentState('complete');
		setTimeout(() => setAgentState('idle'), 2000);
	};

	const handleNonStreamingResponse = async (query: string) => {
		setAgentState('searching');
		await new Promise(resolve => setTimeout(resolve, 500));

		setAgentState('analyzing');
		await new Promise(resolve => setTimeout(resolve, 800));

		setAgentState('generating');

		const response: QueryResponse = await chatApi.query({ query, stream: false });

		const assistantMessage: ChatMessage = {
			role: 'assistant',
			content: response.response,
			timestamp: new Date().toISOString(),
			citations: response.citations,
		};

		setMessages((prev) => [...prev, assistantMessage]);
		setCurrentCitations(response.citations || []);

		setAgentState('complete');
		setTimeout(() => setAgentState('idle'), 2000);
	};

	const clearMessages = () => {
		setMessages([]);
		setCurrentCitations([]);
		setAgentState('idle');
	};

	return {
		messages,
		agentState,
		isLoading,
		currentCitations,
		sendMessage,
		clearMessages,
	};
}
