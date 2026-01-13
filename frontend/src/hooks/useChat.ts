'use client';

import { useState, useEffect, useCallback } from 'react';
import { chatApi, QueryResponse, CitationInfo, ChatMessage as ApiChatMessage } from '@/lib/api/chat';
import { AgentState } from '@/components/chat/AgenticThought';

// Extend the local ChatMessage to match our needs
export interface ChatMessage {
	role: 'user' | 'assistant';
	content: string;
	timestamp: string;
	citations?: CitationInfo[];
}

export interface ChatSession {
	id: string;
	title: string;
	date: string;
	messages: ChatMessage[];
}

export function useChat() {
	const [messages, setMessages] = useState<ChatMessage[]>([]);
	const [agentState, setAgentState] = useState<AgentState>('idle');
	const [isLoading, setIsLoading] = useState(false);
	const [currentCitations, setCurrentCitations] = useState<CitationInfo[]>([]);
	
	// Session Management
	const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
	const [sessions, setSessions] = useState<ChatSession[]>([]);

	// Initial Load: Fetch History
	const fetchHistory = useCallback(async () => {
		try {
			const history = await chatApi.history({ limit: 100 });
			
			// Group messages by sessionId
			const sessionsMap = new Map<string, ChatMessage[]>();
			
			// Sort messages by creation time first just in case
			const sortedMessages = history.messages.sort((a, b) => 
				new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
			);

			sortedMessages.forEach(msg => {
				const sid = msg.sessionId;
				if (!sid) return;
				
				if (!sessionsMap.has(sid)) {
					sessionsMap.set(sid, []);
				}
				
				sessionsMap.get(sid)?.push({
					role: msg.role,
					content: msg.content,
					timestamp: msg.createdAt,
					// Safely handle citations: 
					// 1. If it's already an array (future proof)
					// 2. If it's wrapped in 'sources' (my planned backend change)
					// 3. Else empty (fallback for current simple dict format)
					citations: Array.isArray(msg.citations) ? msg.citations : (msg.citations?.sources || [])
				});
			});

			// Create Session objects
			const loadedSessions: ChatSession[] = Array.from(sessionsMap.entries()).map(([id, msgs]) => {
				// Title is the first user message, or "New Chat"
				const firstUserMsg = msgs.find(m => m.role === 'user');
				const title = firstUserMsg ? firstUserMsg.content.slice(0, 30) + (firstUserMsg.content.length > 30 ? '...' : '') : 'New Chat';
                
                // Date from last message
                const lastMsg = msgs[msgs.length - 1];
                const date = new Date(lastMsg.timestamp).toLocaleDateString();

				return {
					id,
					title,
					date,
					messages: msgs
				};
			});
            
            // Sort sessions by most recent (using the timestamp of the last message in the session)
            loadedSessions.sort((a, b) => {
                 const lastA = new Date(a.messages[a.messages.length - 1].timestamp).getTime();
                 const lastB = new Date(b.messages[b.messages.length - 1].timestamp).getTime();
                 return lastB - lastA;
            });

			setSessions(loadedSessions);
		} catch (error) {
			console.error("Failed to load chat history:", error);
		}
	}, []);

	useEffect(() => {
		fetchHistory();
	}, [fetchHistory]);

	const loadSession = (session: ChatSession) => {
		setCurrentSessionId(session.id);
		setMessages(session.messages);
		
		// Reset other states
		setAgentState('idle');
		// Maybe load citations from the last message if available?
		const lastMsg = session.messages[session.messages.length - 1];
		if (lastMsg?.citations) {
			setCurrentCitations(lastMsg.citations);
		} else {
			setCurrentCitations([]);
		}
	};

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
            // Refresh history to pick up the new session/messages
            // We delay slightly to let the backend index? Or just re-fetch
            setTimeout(fetchHistory, 1000); 
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
			// Pass currentSessionId if it exists
			const stream = chatApi.queryStream({ 
				query, 
				stream: true, 
				sessionId: currentSessionId || undefined 
			});

			for await (const chunk of stream) {
                // If it's the first chunk and we didn't have a session ID, we might want to capture it from response headers?
                // But the stream generator currently only yields strings (content).
                // For now, we rely on the backend reusing the session if we pass it, or creating a new "implicit" one.
                // Re-fetching history after will clarify the session ID.
                
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

		const response: QueryResponse = await chatApi.query({ 
			query, 
			stream: false,
			sessionId: currentSessionId || undefined
		});
        
        // Update current session ID if we started a new one
        if (response.sessionId && !currentSessionId) {
            setCurrentSessionId(response.sessionId);
        }

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
		setCurrentSessionId(null); // Reset session to start a fresh one
	};

	return {
		messages,
		agentState,
		isLoading,
		currentCitations,
		sendMessage,
		clearMessages,
        sessions,
        loadSession,
        currentSessionId
	};
}
