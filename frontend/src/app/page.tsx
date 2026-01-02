'use client';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowRight, Shield, TrendingUp, Zap } from 'lucide-react';

export default function Home() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: { 
        staggerChildren: 0.2,
        delayChildren: 0.3
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { 
      y: 0, 
      opacity: 1,
      transition: { type: 'spring', stiffness: 100 }
    }
  };

  return (
    <motion.div 
      className="container" 
      style={{ marginTop: '2rem' }}
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      <div className="page-center" style={{ minHeight: '60vh' }}>
        <motion.h1 
          variants={itemVariants}
          style={{ 
            fontSize: '4.5rem', 
            marginBottom: '1.5rem', 
            background: 'linear-gradient(to right, #c084fc, #8b5cf6, #6366f1)', 
            WebkitBackgroundClip: 'text', 
            WebkitTextFillColor: 'transparent',
            lineHeight: 1.1,
            textAlign: 'center'
          }}
        >
          Future of Finance<br/> is Here
        </motion.h1>
        
        <motion.p 
          variants={itemVariants}
          style={{ 
            fontSize: '1.25rem', 
            color: '#94a3b8', 
            marginBottom: '4rem', 
            maxWidth: '600px', 
            margin: '0 auto 4rem',
            textAlign: 'center',
            lineHeight: 1.6
          }}
        >
          AI-driven insights to maximize your wealth. Secure, intelligent, and personalized financial planning for the modern era.
        </motion.p>

        <motion.div variants={itemVariants}>
          <Link href="/signup" className="btn-primary" style={{ padding: '1rem 2.5rem', fontSize: '1.125rem' }}>
            Get Started <ArrowRight size={20} />
          </Link>
        </motion.div>
      </div>
      
      <motion.div 
        className="grid-layout" 
        style={{ marginTop: '4rem', marginBottom: '4rem' }}
        variants={containerVariants}
      >
        <motion.div className="glass-card" variants={itemVariants}>
          <div style={{ background: 'rgba(139, 92, 246, 0.1)', padding: '1rem', borderRadius: '1rem', width: 'fit-content' }}>
            <Zap size={32} color="#8b5cf6" />
          </div>
          <h3>Smart Analysis</h3>
          <p style={{ color: '#cbd5e1', lineHeight: 1.6 }}>Our AI analyzes your financial profile in seconds to provide tailored investment strategies that evolve with you.</p>
        </motion.div>

        <motion.div className="glass-card" variants={itemVariants}>
          <div style={{ background: 'rgba(6, 182, 212, 0.1)', padding: '1rem', borderRadius: '1rem', width: 'fit-content' }}>
            <Shield size={32} color="#06b6d4" />
          </div>
          <h3>Data Security</h3>
          <p style={{ color: '#cbd5e1', lineHeight: 1.6 }}>Bank-grade encryption and privacy-first architecture ensure your financial data remains your own.</p>
        </motion.div>

        <motion.div className="glass-card" variants={itemVariants}>
          <div style={{ background: 'rgba(236, 72, 153, 0.1)', padding: '1rem', borderRadius: '1rem', width: 'fit-content' }}>
            <TrendingUp size={32} color="#ec4899" />
          </div>
          <h3>Real-time Insights</h3>
          <p style={{ color: '#cbd5e1', lineHeight: 1.6 }}>Get instant feedback on market trends, portfolio performance, and potential opportunities around the clock.</p>
        </motion.div>
      </motion.div>
    </motion.div>
  )
}
