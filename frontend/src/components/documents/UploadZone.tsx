'use client';

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, AlertCircle, CheckCircle, XCircle } from 'lucide-react';
import { useUploadDocument } from '@/hooks/useDocuments';
import { GlassCard } from '@/components/ui/GlassCard';

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
const ACCEPTED_TYPES = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/plain': ['.txt'],
  'image/png': ['.png'],
  'image/jpeg': ['.jpg', '.jpeg']
};

interface UploadZoneProps {
  onUploadSuccess?: (documentId: string) => void;
}

interface UploadingFile {
  name: string;
  status: 'uploading' | 'success' | 'error';
  error?: string;
}

export default function UploadZone({ onUploadSuccess }: UploadZoneProps) {
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  const uploadMutation = useUploadDocument(onUploadSuccess);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    // Initialize all files as uploading
    setUploadingFiles(acceptedFiles.map(f => ({ name: f.name, status: 'uploading' })));

    // Upload files sequentially to avoid overwhelming the server
    for (let i = 0; i < acceptedFiles.length; i++) {
      const file = acceptedFiles[i];
      try {
        await uploadMutation.mutateAsync(file);
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
  }, [uploadMutation]);

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
          relative rounded-3xl p-10 transition-all duration-300 cursor-pointer group
          border-3 border-dashed
            ? 'border-emerald-500 bg-emerald-500/10 scale-[1.01] shadow-2xl shadow-emerald-500/20' 
            : 'border-emerald-500/30 bg-emerald-500/5 hover:border-emerald-500 hover:bg-emerald-500/10'
          }
          backdrop-blur-xl flex flex-col items-center justify-center text-center gap-6 min-h-[300px]
        `}
      >
        <input {...getInputProps()} />
        
        <div className={`
          p-6 rounded-2xl transition-all duration-300 shadow-xl
          ${isDragActive 
            ? 'bg-accent text-white scale-125 shadow-accent/40' 
            : 'bg-gradient-brand text-white group-hover:scale-110 shadow-blue-500/30'
          }
        `}>
          <Upload className="w-12 h-12" />
        </div>

        <div className="space-y-2 max-w-md mx-auto">
          <h3 className="text-2xl font-bold text-foreground">
            {isDragActive ? 'Drop files now' : 'Upload Documents'}
          </h3>
          <p className="text-foreground-secondary text-base leading-relaxed">
            Drag & drop your files here, or{' '}
            <span className="text-accent font-semibold hover:underline decoration-2 underline-offset-2">browse computer</span>
          </p>
          <p className="pt-2 text-sm font-medium text-foreground-muted opacity-80">
            PDF, DOCX, TXT, PNG, JPG • Max 50MB
          </p>
        </div>

        {uploadingFiles.length > 0 && (
          <div className="w-full max-w-sm space-y-3 mt-2">
            {uploadingFiles.map((file, idx) => (
              <GlassCard
                key={idx}
                className={`p-4 flex items-center justify-between !bg-white/80 dark:!bg-slate-800/80 backdrop-blur-md border !border-gray-200 dark:!border-gray-700
                  ${file.status === 'error' ? '!border-red-500/50 !bg-red-50' : ''}
                  ${file.status === 'success' ? '!border-green-500/50 !bg-green-50' : ''}
                `}
              >
                <div className="flex items-center space-x-3 min-w-0">
                  {file.status === 'uploading' && (
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-accent border-b-transparent"></div>
                  )}
                  {file.status === 'success' && (
                    <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0" />
                  )}
                  {file.status === 'error' && (
                    <XCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
                  )}
                  <span className={`text-sm font-medium truncate ${
                    file.status === 'error' ? 'text-red-700' : 
                    file.status === 'success' ? 'text-green-700' : 'text-foreground'
                  }`}>
                    {file.name}
                  </span>
                </div>
              </GlassCard>
            ))}
          </div>
        )}
      </div>

      {/* File Rejections */}
      {fileRejections.length > 0 && (
        <div className="mt-4 space-y-2">
          {fileRejections.map(({ file, errors }) => (
            <div key={file.name} className="bg-red-500/10 border border-red-500/20 rounded-xl p-4">
              <div className="flex items-start space-x-3">
                <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-red-500">
                    {file.name}
                  </p>
                  {errors.map((error) => (
                    <p key={error.code} className="text-sm text-red-400 mt-1">
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
