'use client';

import { useDocuments, useDeleteDocument } from '@/hooks/useDocuments';
import { FileText, Calendar, Trash2, Download, AlertCircle, Loader2 } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface CompanyDocumentListProps {
  companyId: string;
}

export default function CompanyDocumentList({ companyId }: CompanyDocumentListProps) {
  const { data, isLoading, error } = useDocuments({ 
    company_id: companyId,
    limit: 50 
  });
  
  const deleteMutation = useDeleteDocument();

  if (isLoading) {
    return (
        <div className="flex justify-center p-8">
            <Loader2 className="animate-spin text-gray-500" size={24} />
        </div>
    );
  }

  if (error) {
     return (
        <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-2">
            <AlertCircle size={16} />
            Failed to load documents
        </div>
     );
  }

  if (!data?.documents || data.documents.length === 0) {
    return (
        <div className="text-center py-8 text-gray-500 text-sm">
            No documents found for this company.
        </div>
    );
  }

  return (
    <div className="space-y-3 mt-6">
      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Uploaded Documents</h3>
      {data.documents.map((doc) => (
        <div 
            key={doc.id}
            className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors group"
        >
            <div className="flex items-center gap-4 min-w-0">
                <div className={`p-2.5 rounded-lg ${
                    doc.status === 'PROCESSED' ? 'bg-emerald-500/20 text-emerald-400' :
                    doc.status === 'FAILED' ? 'bg-red-500/20 text-red-400' :
                    'bg-blue-500/20 text-blue-400'
                }`}>
                    <FileText size={20} />
                </div>
                <div className="min-w-0">
                    <h4 className="text-white font-medium truncate pr-4">{doc.filename}</h4>
                    <div className="flex items-center gap-3 text-xs text-gray-400 mt-0.5">
                        <span className="flex items-center gap-1">
                            <Calendar size={12} />
                            {formatDistanceToNow(new Date(doc.uploadDate), { addSuffix: true })}
                        </span>
                        <span className="capitalize px-1.5 py-0.5 rounded-full bg-white/5 border border-white/10 text-[10px]">
                            {doc.status.toLowerCase()}
                        </span>
                    </div>
                </div>
            </div>

            <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                {/* 
                <button className="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors" title="Download">
                    <Download size={16} />
                </button> 
                */}
                <button 
                    onClick={() => {
                        if (confirm('Are you sure you want to delete this document?')) {
                            deleteMutation.mutate(doc.id);
                        }
                    }}
                    className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                    title="Delete"
                >
                    <Trash2 size={16} />
                </button>
            </div>
        </div>
      ))}
    </div>
  );
}
