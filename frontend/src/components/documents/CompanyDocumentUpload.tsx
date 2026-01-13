'use client';

import { useCallback, useState } from 'react';
import { useUploadDocument } from '@/hooks/useDocuments';
import { GlassCard } from '@/components/ui/GlassCard';
import { Upload, AlertCircle, CheckCircle, XCircle } from 'lucide-react';
import { useDropzone } from 'react-dropzone';

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
  onUploadSuccess?: () => void;
}

interface UploadingFile {
  name: string;
  status: 'uploading' | 'success' | 'error';
  error?: string;
}

export default function CompanyDocumentUpload({ companyId, onUploadSuccess }: CompanyDocumentUploadProps) {
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  
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

  const isUploading = uploadingFiles.some(f => f.status === 'uploading');

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxSize: MAX_FILE_SIZE,
    multiple: true,
    disabled: isUploading,
  });

  return (
    <div className="w-full">
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

       {uploadingFiles.length > 0 && (
          <div className="space-y-2 mt-4">
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
        <div className="mt-4 space-y-2">
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
    </div>
  );
}
