import apiClient from '../apiClient';

export interface ChatMessage {
	id: string;
	sessionId: string;
	role: 'user' | 'assistant';
	content: string;
	citations?: any;
	createdAt: string;
}

export interface CitationInfo {
	sourceNumber: number;
	filename: string;
	pageNumber?: number;
	chunkId: string;
	similarity: number;
	text?: string;
	startLine?: number;
	endLine?: number;
}

export interface QueryResponse {
	response: string;
	citations: CitationInfo[];
	sessionId: string;
	tokensUsed?: number;
}

export interface QueryRequest {
	query: string;
	documentIds?: string[];
	maxResults?: number;
	stream?: boolean;
}

export interface ChatHistoryResponse {
	messages: ChatMessage[];
	total: number;
}

export const chatApi = {
	/**
	 * Send a query and get a response (non-streaming)
	 */
	async query(request: QueryRequest): Promise<QueryResponse> {
		const { data } = await apiClient.post<QueryResponse>('/api/v1/chat/query', {
			...request,
			stream: false,
		});
		return data;
	},

	/**
	 * Send a query and get a streaming response
	 */
	async *queryStream(request: QueryRequest): AsyncGenerator<string> {
		const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/chat/query`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'Authorization': `Bearer ${localStorage.getItem('token')}`,
			},
			body: JSON.stringify({
				...request,
				stream: true,
			}),
		});

		if (!response.ok) {
			throw new Error('Stream request failed');
		}

		const reader = response.body?.getReader();
		const decoder = new TextDecoder();

		if (!reader) {
			throw new Error('No reader available');
		}

		while (true) {
			const { done, value } = await reader.read();
			if (done) break;

			const chunk = decoder.decode(value);
			yield chunk;
		}
	},

	/**
	 * Get chat history
	 */
	async history(params?: {
		sessionId?: string;
		skip?: number;
		limit?: number;
	}): Promise<ChatHistoryResponse> {
		const { data } = await apiClient.get<ChatHistoryResponse>('/api/v1/chat/history', {
			params,
		});
		return data;
	},

	/**
	 * Submit feedback on a chat response
	 */
	async feedback(messageId: string, rating: number): Promise<void> {
		await apiClient.post('/api/v1/chat/feedback', {
			message_id: messageId,
			rating,
		});
	},
};
