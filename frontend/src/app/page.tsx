'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  ArrowRight,
  FileText,
  MessageCircle,
  BarChart,
  Shield,
  Zap,
  Lock,
  Sparkles,
} from 'lucide-react';
import { GlassButton } from '@/components/ui/GlassButton';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground overflow-hidden">
      {/* Animated Background */}
      <div className="animated-bg" />

      {/* Navbar */}
      <motion.nav
        className="fixed top-0 left-0 right-0 z-50 glass-navbar"
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
      >
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <Link href="/" className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-primary rounded-xl flex items-center justify-center shadow-lg">
              <span className="font-bold text-white text-lg">M</span>
            </div>
            <span className="text-xl font-bold gradient-text">Mochi</span>
          </Link>

          <div className="flex items-center gap-4">
            <Link href="/login">
              <GlassButton variant="ghost" size="sm">
                Login
              </GlassButton>
            </Link>
            <Link href="/signup">
              <GlassButton variant="primary" size="sm">
                Get Started
              </GlassButton>
            </Link>
          </div>
        </div>
      </motion.nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center px-6 pt-24">
        <div className="max-w-6xl mx-auto text-center">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-card-static mb-8"
          >
            <Sparkles size={16} className="text-accent" />
            <span className="text-sm font-medium text-foreground-secondary">
              AI-Powered Financial Analysis
            </span>
          </motion.div>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-5xl md:text-7xl font-bold tracking-tight mb-6"
          >
            <span className="gradient-text">Smart Finance</span>
            <br />
            <span className="text-foreground">Made Simple</span>
          </motion.h1>

          {/* Subheadline */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-xl text-foreground-muted max-w-2xl mx-auto mb-10 leading-relaxed"
          >
            Upload your financial documents, ask questions in natural language,
            and get instant AI-powered insights with full source citations.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Link href="/signup">
              <GlassButton variant="primary" size="lg" rightIcon={<ArrowRight size={20} />}>
                Start Free Trial
              </GlassButton>
            </Link>
            <Link href="/login">
              <GlassButton variant="secondary" size="lg">
                View Demo
              </GlassButton>
            </Link>
          </motion.div>

          {/* Hero Glass Card */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.5 }}
            className="mt-16 glass-card p-1 max-w-4xl mx-auto"
          >
            <div className="aspect-video rounded-lg bg-gradient-to-br from-accent/20 to-accent-light/10 flex items-center justify-center">
              <div className="text-center p-8">
                <MessageCircle size={48} className="text-accent mx-auto mb-4" />
                <p className="text-foreground-secondary">
                  Interactive Demo Preview
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Everything you need for{' '}
              <span className="gradient-text">financial intelligence</span>
            </h2>
            <p className="text-foreground-muted max-w-2xl mx-auto">
              Powerful features designed to help you understand your finances better
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <FeatureCard
              icon={FileText}
              title="Smart Document Upload"
              description="Drag-and-drop PDFs with automatic text extraction, OCR for images, and secure cloud storage."
              delay={0.1}
            />
            <FeatureCard
              icon={MessageCircle}
              title="AI Chat Assistant"
              description="Ask questions in natural language and get accurate answers with source citations."
              delay={0.2}
            />
            <FeatureCard
              icon={BarChart}
              title="Visual Analytics"
              description="Beautiful dashboards and charts to visualize your financial data at a glance."
              delay={0.3}
            />
            <FeatureCard
              icon={Shield}
              title="Enterprise Security"
              description="Bank-grade encryption, secure authentication, and full audit trails."
              delay={0.4}
            />
            <FeatureCard
              icon={Zap}
              title="Lightning Fast"
              description="Powered by the latest AI models for instant responses and real-time analysis."
              delay={0.5}
            />
            <FeatureCard
              icon={Lock}
              title="Privacy First"
              description="Your data stays yours. We never share or sell your financial information."
              delay={0.6}
            />
          </div>
        </div>
      </section>

      {/* Trust Section */}
      <section className="py-24 px-6 border-t border-glass-border">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="glass-card p-12"
          >
            <h3 className="text-2xl md:text-3xl font-bold mb-6">
              Ready to transform your financial workflow?
            </h3>
            <p className="text-foreground-muted mb-8 max-w-xl mx-auto">
              Join thousands of users who are already using Mochi to manage their
              financial documents more efficiently.
            </p>
            <Link href="/signup">
              <GlassButton variant="primary" size="lg" rightIcon={<ArrowRight size={20} />}>
                Get Started for Free
              </GlassButton>
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-glass-border">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-primary rounded-lg flex items-center justify-center">
              <span className="font-bold text-white text-sm">M</span>
            </div>
            <span className="font-semibold text-foreground">Mochi</span>
          </div>
          <p className="text-sm text-foreground-muted">
            © 2026 Mochi Finance. Built with Next.js & Python.
          </p>
          <div className="flex items-center gap-4">
            <Link href="/login" className="text-sm text-foreground-muted hover:text-accent transition-colors">
              Login
            </Link>
            <Link href="/signup" className="text-sm text-foreground-muted hover:text-accent transition-colors">
              Sign Up
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({
  icon: Icon,
  title,
  description,
  delay = 0,
}: {
  icon: React.ElementType;
  title: string;
  description: string;
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay }}
      className="glass-card group cursor-default"
    >
      <div className="w-12 h-12 rounded-xl bg-blue-500/10 dark:bg-accent/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
        <Icon size={24} className="text-accent" />
      </div>
      <h3 className="text-lg font-semibold mb-2 text-foreground">{title}</h3>
      <p className="text-foreground-muted text-sm leading-relaxed">{description}</p>
    </motion.div>
  );
}
