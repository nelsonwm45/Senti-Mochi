import apiClient from '../apiClient';

export interface Document {
	id: string;
	userId: string;
	filename: string;
	contentType: string;
	fileSize: number;
	status: 'PENDING' | 'PROCESSING' | 'PROCESSED' | 'FAILED';
	uploadDate: string;
	processingStarted?: string;
	processingCompleted?: string;
	errorMessage?: string;
}

export interface DocumentListResponse {
	documents: Document[];
	total: number;
}

export const documentsApi = {
	/**
	 * Upload a new document
	 */
	async upload(file: File): Promise<Document> {
		const formData = new FormData();
		formData.append('file', file);

		const { data } = await apiClient.post<Document>('/api/v1/documents/upload', formData, {
			headers: {
				'Content-Type': 'multipart/form-data',
			},
		});
		return data;
	},

	/**
	 * List documents with pagination and filtering
	 */
	async list(params?: {
		skip?: number;
		limit?: number;
		status?: string;
	}): Promise<DocumentListResponse> {
		const { data } = await apiClient.get<DocumentListResponse>('/api/v1/documents/', {
			params,
		});
		return data;
	},

	/**
	 * Get a single document by ID
	 */
	async get(id: string): Promise<Document> {
		const { data } = await apiClient.get<Document>(`/api/v1/documents/${id}`);
		return data;
	},

	/**
	 * Delete a document (soft delete)
	 */
	async delete(id: string): Promise<void> {
		await apiClient.delete(`/api/v1/documents/${id}`);
	},

	/**
	 * Reprocess a failed document
	 */
	async reprocess(id: string): Promise<void> {
		await apiClient.post(`/api/v1/documents/${id}/reprocess`);
	},

	/**
	 * Get full document content
	 */
	async getContent(id: string): Promise<{ chunks: Array<{ content: string; start_line: number; end_line: number; page_number?: number }> }> {
		const { data } = await apiClient.get<{ chunks: Array<{ content: string; start_line: number; end_line: number; page_number?: number }> }>(`/api/v1/documents/${id}/content`);
		return data;
	},
};
