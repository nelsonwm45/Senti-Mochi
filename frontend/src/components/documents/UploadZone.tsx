'use client';

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, AlertCircle, CheckCircle, XCircle } from 'lucide-react';
import { useUploadDocument } from '@/hooks/useDocuments';

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
          relative border-2 border-dashed rounded-2xl p-12
          transition-all duration-300 cursor-pointer
          ${isDragActive 
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-950/20 scale-105' 
            : 'border-gray-300 dark:border-gray-700 hover:border-blue-400 dark:hover:border-blue-600'
          }
        `}
      >
        <input {...getInputProps()} />
        
        <div className="flex flex-col items-center justify-center space-y-4">
          <div className={`
            p-6 rounded-full transition-colors duration-300
            ${isDragActive 
              ? 'bg-blue-500' 
              : 'bg-gradient-to-br from-blue-500 to-purple-600'
            }
          `}>
            <Upload className="w-12 h-12 text-white" />
          </div>

          <div className="text-center">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              {isDragActive ? 'Drop files here' : 'Upload Documents'}
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Drag & drop your files or{' '}
              <span className="text-blue-500 font-medium">browse</span>
            </p>
            <p className="mt-2 text-sm text-gray-400">
              Supports PDF, DOCX, TXT, PNG, JPG • Max 50MB
            </p>
          </div>

          {uploadingFiles.length > 0 && (
            <div className="w-full max-w-md space-y-2">
              {uploadingFiles.map((file, idx) => (
                <div
                  key={idx}
                  className={`rounded-lg p-3 ${
                    file.status === 'uploading'
                      ? 'bg-blue-100 dark:bg-blue-900/30'
                      : file.status === 'success'
                      ? 'bg-green-100 dark:bg-green-900/30'
                      : 'bg-red-100 dark:bg-red-900/30'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    {file.status === 'uploading' && (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                    )}
                    {file.status === 'success' && (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    )}
                    {file.status === 'error' && (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                    <span className={`text-sm truncate ${
                      file.status === 'uploading'
                        ? 'text-blue-700 dark:text-blue-300'
                        : file.status === 'success'
                        ? 'text-green-700 dark:text-green-300'
                        : 'text-red-700 dark:text-red-300'
                    }`}>
                      {file.name}
                      {file.status === 'uploading' && ' - Uploading...'}
                      {file.status === 'success' && ' - Done'}
                      {file.status === 'error' && ` - ${file.error}`}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* File Rejections */}
      {fileRejections.length > 0 && (
        <div className="mt-4 space-y-2">
          {fileRejections.map(({ file, errors }) => (
            <div key={file.name} className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-red-800 dark:text-red-300">
                    {file.name}
                  </p>
                  {errors.map((error) => (
                    <p key={error.code} className="text-sm text-red-600 dark:text-red-400 mt-1">
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
