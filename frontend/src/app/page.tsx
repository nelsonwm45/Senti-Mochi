'use client';

import Link from 'next/link';
import { ArrowRight, Shield, Zap, FileText, MessageCircle, BarChart } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 text-white">
      {/* Navbar Overlay */}
      <nav className="absolute top-10 left-0 right-0 z-50">
        <div className="container mx-auto px-6 py-6 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
              <span className="font-bold text-white text-lg">SF</span>
            </div>
            <span className="text-2xl font-bold tracking-tight text-white">Secure Finance</span>
          </div>
          <div className="flex items-center space-x-6">
            <Link href="/login" className="text-gray-300 hover:text-white transition-colors font-medium">
              Login
            </Link>
            <Link
              href="/dashboard"
              className="px-5 py-2.5 bg-white text-gray-900 rounded-full font-semibold hover:bg-gray-100 transition-all hover:scale-105 shadow-md"
            >
              Dashboard
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="relative min-h-screen flex flex-col justify-center items-center text-center px-4 pt-20">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-purple-500/10 rounded-full blur-[100px]" />
          <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-500/10 rounded-full blur-[100px]" />
        </div>
        
        <div className="relative z-10 max-w-4xl mx-auto space-y-8">
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6">
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400">
              AI-Powered
            </span>
            <br />
            <span className="text-white">Financial Intelligence</span>
          </h1>
          
          <p className="text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed">
            Securely analyze your financial documents with advanced RAG technology.
            Get instant answers, deep insights, and automated processing.
          </p>
          
          <div className="flex flex-col sm:flex-row justify-center items-center gap-4 pt-4">
            <Link href="/dashboard">
              <button className="px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full font-bold text-lg text-white hover:scale-105 hover:shadow-lg hover:shadow-purple-500/25 transition-all flex items-center">
                Get Started
                <ArrowRight className="w-5 h-5 ml-2" />
              </button>
            </Link>
          </div>
        </div>
      </div>

      {/* Features Grid */}
      <div className="container mx-auto px-4 py-24 border-t border-gray-800/50">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
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
      <footer className="border-t border-gray-800/50 py-12 text-center">
        <p className="text-gray-500">© 2026 Secure Finance RAG. Built with Next.js & Python.</p>
      </footer>
    </div>
  );
}

function FeatureCard({ icon: Icon, title, description }: { icon: any, title: string, description: string }) {
  return (
    <div className="bg-gray-800/30 p-8 rounded-3xl border border-gray-700/50 hover:border-blue-500/50 hover:bg-gray-800/50 transition-all group backdrop-blur-sm">
      <div className="w-14 h-14 bg-blue-500/10 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
        <Icon className="w-7 h-7 text-blue-400" />
      </div>
      <h3 className="text-xl font-bold mb-3 text-white">{title}</h3>
      <p className="text-gray-400 leading-relaxed">
        {description}
      </p>
    </div>
  );
}
