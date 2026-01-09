'use client';

import Link from 'next/link';
import { ArrowRight, Shield, Zap, FileText, MessageCircle, BarChart } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 text-white">
      {/* Navbar Overlay */}
      <div className="absolute top-0 left-0 right-0 p-6 flex justify-between items-center z-10">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
            <span className="font-bold text-sm">SF</span>
          </div>
          <span className="text-xl font-bold">Secure Finance</span>
        </div>
        <div className="space-x-4">
          <Link href="/login" className="text-gray-300 hover:text-white transition-colors">
            Login
          </Link>
          <Link
            href="/dashboard"
            className="bg-white text-gray-900 px-4 py-2 rounded-lg font-medium hover:bg-gray-100 transition-colors"
          >
            Go to Dashboard
          </Link>
        </div>
      </div>

      {/* Hero Section */}
      <div className="container mx-auto px-4 pt-32 pb-20 text-center">
        <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400">
          AI-Powered Financial Intelligence
        </h1>
        <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-12">
          Securely analyze your financial documents with advanced RAG technology.
          Get instant answers, deep insights, and automated processing.
        </p>
        
        <div className="flex flex-col sm:flex-row justify-center space-y-4 sm:space-y-0 sm:space-x-4">
          <Link href="/dashboard">
            <button className="w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl font-bold text-lg hover:scale-105 transition-transform flex items-center justify-center">
              Get Started
              <ArrowRight className="w-5 h-5 ml-2" />
            </button>
          </Link>
          <Link href="/documents">
            <button className="w-full sm:w-auto px-8 py-4 bg-gray-800 border border-gray-700 rounded-xl font-bold text-lg hover:bg-gray-700 transition-colors flex items-center justify-center">
              Upload Documents
            </button>
          </Link>
        </div>
      </div>

      {/* Features Grid */}
      <div className="container mx-auto px-4 py-20">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <FeatureCard
            icon={FileText}
            title="Smart Ingestion"
            description="Drag-and-drop PDF upload with automated text extraction and secure storage."
          />
          <FeatureCard
            icon={MessageCircle}
            title="Agentic Chat"
            description="Ask questions and watch the AI research, analyze, and cite sources in real-time."
          />
          <FeatureCard
            icon={BarChart}
            title="Deep Analytics"
            description="Visualize your document data and get insights through an interactive dashboard."
          />
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-12 text-center text-gray-500">
        <p>© 2026 Secure Finance RAG. Built with Next.js & Python.</p>
      </footer>
    </div>
  );
}

function FeatureCard({ icon: Icon, title, description }: { icon: any, title: string, description: string }) {
  return (
    <div className="bg-gray-800/50 p-8 rounded-2xl border border-gray-700 hover:border-blue-500/50 transition-colors">
      <div className="w-12 h-12 bg-blue-500/10 rounded-xl flex items-center justify-center mb-6">
        <Icon className="w-6 h-6 text-blue-400" />
      </div>
      <h3 className="text-xl font-bold mb-3 text-white">{title}</h3>
      <p className="text-gray-400 leading-relaxed">
        {description}
      </p>
    </div>
  );
}
