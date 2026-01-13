import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { documentsApi, Document } from '../lib/api/documents';
import { toast } from 'react-hot-toast';

/**
 * Hook to fetch list of documents
 */
export function useDocuments(params?: {
	skip?: number;
	limit?: number;
	status?: string;
	company_id?: string;
}) {
	return useQuery({
		queryKey: ['documents', params],
		queryFn: () => documentsApi.list(params),
		refetchInterval: (query) => {
			const data = query.state.data;
			// Auto-refresh if any documents are processing
			const hasProcessing = data?.documents?.some(
				(doc: Document) => doc.status === 'PENDING' || doc.status === 'PROCESSING'
			);
			return hasProcessing ? 3000 : false; // Poll every 3s if processing
		},
	});
}

/**
 * Hook to fetch a single document
 */
export function useDocument(id: string) {
	return useQuery({
		queryKey: ['document', id],
		queryFn: () => documentsApi.get(id),
		enabled: !!id,
	});
}

/**
 * Hook to upload a document
 */
export function useUploadDocument(onSuccess?: (documentId: string) => void) {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: ({ file, companyId }: { file: File; companyId?: string }) =>
			documentsApi.upload(file, companyId),
		onSuccess: (data) => {
			queryClient.invalidateQueries({ queryKey: ['documents'] });
			toast.success('Document uploaded successfully!');
			if (onSuccess && data.id) {
				onSuccess(data.id);
			}
		},
		onError: (error: any) => {
			const detail = error.response?.data?.detail;
			const message = typeof detail === 'string'
				? detail
				: Array.isArray(detail)
					? detail.map((d: any) => d.msg).join(', ')
					: error.message || 'Upload failed';
			toast.error(message);
		},
	});
}

/**
 * Hook to delete a document
 */
export function useDeleteDocument() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: (id: string) => documentsApi.delete(id),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ['documents'] });
			toast.success('Document deleted');
		},
		onError: (error: any) => {
			const detail = error.response?.data?.detail;
			const message = typeof detail === 'string'
				? detail
				: Array.isArray(detail)
					? detail.map((d: any) => d.msg).join(', ')
					: error.message || 'Delete failed';
			toast.error(message);
		},
	});
}

/**
 * Hook to reprocess a document
 */
export function useReprocessDocument() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: (id: string) => documentsApi.reprocess(id),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ['documents'] });
			toast.success('Reprocessing started');
		},
		onError: (error: any) => {
			const detail = error.response?.data?.detail;
			const message = typeof detail === 'string'
				? detail
				: Array.isArray(detail)
					? detail.map((d: any) => d.msg).join(', ')
					: error.message || 'Reprocess failed';
			toast.error(message);
		},
	});
}

/**
 * Hook to fetch document content
 */
export function useDocumentContent(id: string) {
	return useQuery({
		queryKey: ['documentContent', id],
		queryFn: () => documentsApi.getContent(id),
		enabled: !!id,
	});
}
