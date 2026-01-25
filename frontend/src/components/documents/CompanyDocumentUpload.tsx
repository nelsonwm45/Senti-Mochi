'use client';

import { useCallback, useState } from 'react';
import { useUploadDocument, useDocuments, useDeleteDocument } from '@/hooks/useDocuments';
import { GlassCard } from '@/components/ui/GlassCard';
import { Upload, AlertCircle, CheckCircle, XCircle, FileText, Trash2, Loader2, ExternalLink } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import { Document } from '@/lib/api/documents';

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
const ACCEPTED_TYPES = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/plain': ['.txt'],
  'image/png': ['.png'],
  'image/jpeg': ['.jpg', '.jpeg']
};

interface CompanyDocumentUploadProps {
  companyId: string;
  companyTicker?: string;
  onUploadSuccess?: () => void;
}

interface UploadingFile {
  name: string;
  status: 'uploading' | 'success' | 'error';
  error?: string;
}

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'PROCESSED':
      return <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">Ready</span>;
    case 'PROCESSING':
      return <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center gap-1"><Loader2 size={10} className="animate-spin" /> Processing</span>;
    case 'PENDING':
      return <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">Pending</span>;
    case 'FAILED':
      return <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-red-500/20 text-red-400 border border-red-500/30">Failed</span>;
    default:
      return <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-gray-500/20 text-gray-400 border border-gray-500/30">{status}</span>;
  }
};

export default function CompanyDocumentUpload({ companyId, companyTicker, onUploadSuccess }: CompanyDocumentUploadProps) {
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Fetch existing documents for this company
  const { data: documentsData, isLoading: isLoadingDocs } = useDocuments({ company_id: companyId });
  const existingDocs = documentsData?.documents || [];

  // Delete mutation
  const deleteMutation = useDeleteDocument();

  // Pass success callback to invalidate queries, but we also want to trigger parent refresh potentially
  const uploadMutation = useUploadDocument((docId) => {
    if (onUploadSuccess) onUploadSuccess();
  });

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    // Initialize all files as uploading
    setUploadingFiles(acceptedFiles.map(f => ({ name: f.name, status: 'uploading' })));

    // Upload files sequentially
    for (let i = 0; i < acceptedFiles.length; i++) {
      const file = acceptedFiles[i];
      try {
        await uploadMutation.mutateAsync({ file, companyId });
        setUploadingFiles(prev =>
          prev.map((f, idx) => idx === i ? { ...f, status: 'success' } : f)
        );
      } catch (error: any) {
        setUploadingFiles(prev =>
          prev.map((f, idx) => idx === i ? { ...f, status: 'error', error: error?.message || 'Upload failed' } : f)
        );
      }
    }

    // Clear the upload status after 3 seconds
    setTimeout(() => setUploadingFiles([]), 3000);
  }, [uploadMutation, companyId]);

  const handleDelete = async (docId: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    setDeletingId(docId);
    try {
      await deleteMutation.mutateAsync(docId);
    } finally {
      setDeletingId(null);
    }
  };

  const isUploading = uploadingFiles.some(f => f.status === 'uploading');

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxSize: MAX_FILE_SIZE,
    multiple: true,
    disabled: isUploading,
  });

  return (
    <div className="w-full space-y-4">
      {/* Header with company ticker */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">Upload Documents {companyTicker ? `for ${companyTicker}` : ''}</h3>
        <span className="text-xs text-gray-500">{existingDocs.length} document{existingDocs.length !== 1 ? 's' : ''}</span>
      </div>

      {/* Upload Dropzone */}
      <div
        {...getRootProps()}
        className={`
          relative rounded-2xl p-8 transition-all duration-300 cursor-pointer group
          border-2 border-dashed
            ${isDragActive
            ? 'border-emerald-500 bg-emerald-500/10 scale-[1.01] shadow-2xl shadow-emerald-500/20'
            : 'border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/10'
          }
          flex flex-col items-center justify-center text-center gap-4 min-h-[200px]
        `}
      >
        <input {...getInputProps()} />

        <div className={`
          p-4 rounded-xl transition-all duration-300 shadow-lg
          ${isDragActive
            ? 'bg-accent text-white scale-110'
            : 'bg-white/10 text-gray-300 group-hover:scale-105 group-hover:bg-white/20 group-hover:text-white'
          }
        `}>
          <Upload className="w-8 h-8" />
        </div>

        <div className="space-y-1">
          <h3 className="text-lg font-semibold text-white">
            {isDragActive ? 'Drop files now' : 'Upload Documents'}
          </h3>
          <p className="text-gray-400 text-sm">
            Drag & drop or <span className="text-emerald-400 hover:underline">browse</span>
          </p>
        </div>
      </div>

      {/* Uploading Files Status */}
      {uploadingFiles.length > 0 && (
        <div className="space-y-2">
          {uploadingFiles.map((file, idx) => (
            <div
              key={idx}
              className={`p-3 rounded-lg flex items-center justify-between border
                ${file.status === 'error' ? 'border-red-500/30 bg-red-500/10' : ''}
                ${file.status === 'success' ? 'border-emerald-500/30 bg-emerald-500/10' : ''}
                ${file.status === 'uploading' ? 'border-white/10 bg-white/5' : ''}
              `}
            >
              <div className="flex items-center space-x-3 min-w-0">
                {file.status === 'uploading' && (
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-accent border-b-transparent"></div>
                )}
                {file.status === 'success' && (
                  <CheckCircle className="h-4 w-4 text-emerald-500 flex-shrink-0" />
                )}
                {file.status === 'error' && (
                  <XCircle className="h-4 w-4 text-red-500 flex-shrink-0" />
                )}
                <span className={`text-sm font-medium truncate ${
                  file.status === 'error' ? 'text-red-400' :
                  file.status === 'success' ? 'text-emerald-400' : 'text-gray-300'
                }`}>
                  {file.name}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* File Rejections */}
      {fileRejections.length > 0 && (
        <div className="space-y-2">
          {fileRejections.map(({ file, errors }) => (
            <div key={file.name} className="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
              <div className="flex items-start space-x-3">
                <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-red-500">
                    {file.name}
                  </p>
                  {errors.map((error) => (
                    <p key={error.code} className="text-xs text-red-400 mt-0.5">
                      {error.message}
                    </p>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Existing Documents List */}
      <div className="space-y-2">
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Uploaded Documents</h4>

        {isLoadingDocs ? (
          <div className="flex items-center justify-center py-8 text-gray-500">
            <Loader2 size={20} className="animate-spin mr-2" />
            Loading documents...
          </div>
        ) : existingDocs.length === 0 ? (
          <div className="text-center py-8 text-gray-500 text-sm border border-white/5 rounded-lg bg-white/[0.02]">
            No documents uploaded yet for this company.
          </div>
        ) : (
          <div className="space-y-2 max-h-[300px] overflow-y-auto custom-scrollbar pr-1">
            {existingDocs.map((doc: Document) => (
              <div
                key={doc.id}
                className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/10 hover:border-white/20 transition-colors group"
              >
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <div className="w-8 h-8 rounded-lg bg-indigo-500/20 flex items-center justify-center flex-shrink-0">
                    <FileText size={16} className="text-indigo-400" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-white truncate" title={doc.filename}>
                      {doc.filename}
                    </p>
                    <div className="flex items-center gap-2 mt-0.5">
                      {getStatusBadge(doc.status)}
                      {doc.chunk_count !== undefined && doc.chunk_count > 0 && (
                        <span className="text-[10px] text-gray-500">{doc.chunk_count} chunks</span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  {/* Download link */}
                  {doc.status === 'PROCESSED' && (
                    <a
                      href={`/api/v1/documents/${doc.id}/download`}
                      className="p-1.5 rounded-lg text-gray-500 hover:text-blue-400 hover:bg-blue-500/10 transition-colors"
                      title="Download"
                      onClick={(e) => {
                        e.preventDefault();
                        // Use authenticated download
                        const token = localStorage.getItem('token');
                        fetch(`/api/v1/documents/${doc.id}/download`, {
                          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
                        })
                        .then(res => res.blob())
                        .then(blob => {
                          const url = window.URL.createObjectURL(blob);
                          const a = document.createElement('a');
                          a.href = url;
                          a.download = doc.filename;
                          a.click();
                          window.URL.revokeObjectURL(url);
                        })
                        .catch(() => alert('Download failed'));
                      }}
                    >
                      <ExternalLink size={14} />
                    </a>
                  )}

                  {/* Delete button */}
                  <button
                    onClick={() => handleDelete(doc.id)}
                    disabled={deletingId === doc.id}
                    className="p-1.5 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-colors disabled:opacity-50"
                    title="Delete document"
                  >
                    {deletingId === doc.id ? (
                      <Loader2 size={14} className="animate-spin" />
                    ) : (
                      <Trash2 size={14} />
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
