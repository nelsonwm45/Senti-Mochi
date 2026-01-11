import React from 'react';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-background text-foreground overflow-hidden relative flex items-center justify-center p-4">
      {/* Animated Background */}
      <div className="animated-bg" />
      
      {/* Back Button */}
      <Link 
        href="/" 
        className="absolute top-8 left-8 flex items-center space-x-2 text-foreground-muted hover:text-foreground transition-colors group z-20"
      >
        <div className="p-2 glass-button rounded-full group-hover:bg-white/10 transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </div>
        <span className="font-medium text-sm">Back to Home</span>
      </Link>

      {/* Content */}
      <div className="w-full relative z-10 flex flex-col items-center justify-center">
        {children}
      </div>
    </div>
  );
}
