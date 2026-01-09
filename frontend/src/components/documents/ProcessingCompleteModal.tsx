'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, FileText, X, ArrowRight } from 'lucide-react';
import { Document } from '@/lib/api/documents';
import Link from 'next/link';

interface ProcessingCompleteModalProps {
  isOpen: boolean;
  onClose: () => void;
  document: Document | null;
}

export default function ProcessingCompleteModal({
  isOpen,
  onClose,
  document,
}: ProcessingCompleteModalProps) {
  if (!document) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 z-50 backdrop-blur-sm"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: 'spring', duration: 0.5 }}
            className="fixed inset-0 flex items-center justify-center z-50 pointer-events-none"
          >
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 w-full max-w-md p-6 pointer-events-auto mx-4">
              
              {/* Header */}
              <div className="flex items-start justify-between mb-6">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-full">
                    <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      Processing Complete
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Your document is ready to use
                    </p>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Document Info Card */}
              <div className="bg-gray-50 dark:bg-gray-900/50 rounded-xl p-4 mb-6 border border-gray-100 dark:border-gray-800">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
                    <FileText className="w-6 h-6 text-blue-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {document.filename}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {(document.fileSize / 1024).toFixed(1)} KB • {new Date(document.uploadDate).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex space-x-3">
                <button
                  onClick={onClose}
                  className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 font-medium rounded-xl hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                >
                  Close
                </button>
                <Link
                  href={`/documents?view=${document.id}`}
                  className="flex-1 px-4 py-2.5 bg-blue-600 text-white font-medium rounded-xl hover:bg-blue-700 transition-colors flex items-center justify-center space-x-2"
                >
                  <span>View Document</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
