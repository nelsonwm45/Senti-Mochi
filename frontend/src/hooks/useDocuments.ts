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
}) {
	return useQuery({
		queryKey: ['documents', params],
		queryFn: () => documentsApi.list(params),
		refetchInterval: (data) => {
			// Auto-refresh if any documents are processing
			const hasProcessing = data?.documents.some(
				(doc) => doc.status === 'PENDING' || doc.status === 'PROCESSING'
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
export function useUploadDocument() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: (file: File) => documentsApi.upload(file),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ['documents'] });
			toast.success('Document uploaded successfully!');
		},
		onError: (error: any) => {
			toast.error(error.response?.data?.detail || 'Upload failed');
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
			toast.error(error.response?.data?.detail || 'Delete failed');
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
			toast.error(error.response?.data?.detail || 'Reprocess failed');
		},
	});
}
