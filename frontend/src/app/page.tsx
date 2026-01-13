'use client';

import Link from 'next/link';
import Image from 'next/image';
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
  ListChecks,
  Rss,
  Database,
  Newspaper,
  TrendingUp,
  Bot,
  RefreshCw,
  ThumbsUp,
  FileCheck,
  User,
  Search,
  ShieldCheck,
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
            <div className="relative w-10 h-10 flex-shrink-0">
              <Image
                src="/MochiTrio.png"
                alt="Mochi Logo"
                fill
                className="object-contain"
                priority
              />
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
              Market Intelligence Platform
            </span>
          </motion.div>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-5xl md:text-7xl font-bold tracking-tight mb-6"
          >
            <span className="gradient-text">Market Intelligence</span>
            <br />
            <span className="text-foreground">Made Reliable</span>
          </motion.h1>

          {/* Subheadline */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-xl text-foreground-muted max-w-2xl mx-auto mb-10 leading-relaxed"
          >
            An end-to-end workflow that helps bank teams cut through noisy, unstructured market signals and make consistent, defensible decisions.
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
                Get Started
              </GlassButton>
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Workflow Overview Section */}
      <section className="py-24 px-6 border-t border-glass-border">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              How it <span className="gradient-text">works</span>
            </h2>
            <p className="text-foreground-muted max-w-2xl mx-auto">
              A simple three-step workflow to transform market signals into actionable intelligence
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <WorkflowStep
              icon={ListChecks}
              step="1"
              title="Watchlists"
              description="Users add Bursa-listed companies to a watchlist so the system monitors only relevant entities."
              delay={0.1}
            />
            <WorkflowStep
              icon={Rss}
              step="2"
              title="Live Source Ingestion"
              description="News, announcements, and reports are continuously pulled from credible sources such as Bursa, NST, and The Star."
              delay={0.2}
            />
            <WorkflowStep
              icon={Database}
              step="3"
              title="Processing & Storage"
              description="All documents are parsed, enriched (sentiment, entities), and stored in a vector database to support search, analysis, and traceability."
              delay={0.3}
            />
          </div>
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
              Key <span className="gradient-text">capabilities</span>
            </h2>
            <p className="text-foreground-muted max-w-2xl mx-auto">
              Powerful features designed to help bank teams make consistent, defensible decisions
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <FeatureCard
              icon={Newspaper}
              title="Dashboard News Feed"
              description="Company-specific news tagged with consistent sentiment (positive/negative/neutral), alerts for critical issues, and AI summaries with links back to original sources."
              delay={0.1}
            />
            <FeatureCard
              icon={TrendingUp}
              title="Company Watchlist"
              description="Standardized financial metrics for side-by-side comparison across companies and time, with support for manual document uploads to enrich company context."
              delay={0.2}
            />
            <FeatureCard
              icon={Bot}
              title="AI Copilot"
              description="Ask questions about companies or industries. Answers generated only from ingested data with full citations provided for every insight."
              delay={0.3}
            />
            <FeatureCard
              icon={RefreshCw}
              title="Live Source Integration"
              description="Real-time ingestion from Bursa Malaysia, New Straits Times, and The Star to ensure you never miss critical market signals."
              delay={0.4}
            />
            <FeatureCard
              icon={ThumbsUp}
              title="Sentiment Analysis"
              description="Automated sentiment tagging for consistent signal interpretation, helping teams cut through noise and focus on what matters."
              delay={0.5}
            />
            <FeatureCard
              icon={FileCheck}
              title="Evidence Trail"
              description="Full traceability with citations for defensible decisions. Every insight links back to its source for complete transparency."
              delay={0.6}
            />
          </div>
        </div>
      </section>

      {/* Who It's For Section */}
      <section className="py-24 px-6 border-t border-glass-border">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Who it's <span className="gradient-text">for</span>
            </h2>
            <p className="text-foreground-muted max-w-2xl mx-auto">
              Built for bank teams who need fast, reliable market intelligence
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <PersonaCard
              icon={User}
              title="Relationship Managers / Coverage Teams"
              description="Get fast, reliable context before client engagements."
              delay={0.1}
            />
            <PersonaCard
              icon={Search}
              title="Market Intelligence & Research Analysts"
              description="Reduce manual scanning and work from consistent, structured signals."
              delay={0.2}
            />
            <PersonaCard
              icon={ShieldCheck}
              title="Credit & Risk Stakeholders"
              description="Access standardized financial data and defend decisions with clear evidence trails."
              delay={0.3}
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
              Ready to transform your market intelligence workflow?
            </h3>
            <p className="text-foreground-muted mb-8 max-w-xl mx-auto">
              Join bank teams who are using Mochi to cut through market noise and make defensible decisions faster.
            </p>
            <Link href="/signup">
              <GlassButton variant="primary" size="lg" rightIcon={<ArrowRight size={20} />}>
                Get Started Now
              </GlassButton>
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-glass-border">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="relative w-8 h-8 flex-shrink-0">
              <Image
                src="/MochiTrio.png"
                alt="Mochi Logo"
                fill
                className="object-contain"
              />
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

function WorkflowStep({
  icon: Icon,
  step,
  title,
  description,
  delay = 0,
}: {
  icon: React.ElementType;
  step: string;
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
      <div className="flex items-center gap-3 mb-4">
        <div className="w-8 h-8 rounded-lg bg-gradient-primary flex items-center justify-center text-white font-bold text-sm">
          {step}
        </div>
        <div className="w-12 h-12 rounded-xl bg-blue-500/10 dark:bg-accent/10 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
          <Icon size={24} className="text-accent" />
        </div>
      </div>
      <h3 className="text-lg font-semibold mb-2 text-foreground">{title}</h3>
      <p className="text-foreground-muted text-sm leading-relaxed">{description}</p>
    </motion.div>
  );
}

function PersonaCard({
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
