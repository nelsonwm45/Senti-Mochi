'use client';
import { useState, useEffect } from 'react';
import axios from 'axios';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Mail, Lock, UserPlus, ArrowRight, User } from 'lucide-react';
import Link from 'next/link';

import { setToken, getToken } from '@/lib/auth';

export default function Signup() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const router = useRouter();

  useEffect(() => {
    if (getToken()) {
      router.push('/dashboard');
    }
  }, [router]);

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      alert('Passwords do not match');
      return;
    }

    try {
      const res = await axios.post('http://localhost:8000/auth/signup', {
        email: email,
        password: password,
        full_name: fullName
      });
      setToken(res.data.access_token);
      
      router.push('/dashboard');
    } catch (err) {
      alert('Signup failed');
    }
  };

  return (
    <div className="container page-center">
      <motion.div
        className="glass-card signup-card"
        style={{ width: '100%', maxWidth: '420px' }}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Header Section */}
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            <div style={{
              width: '64px',
              height: '64px',
              margin: '0 auto 1rem',
              background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
              borderRadius: '16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 8px 16px rgba(139, 92, 246, 0.3)',
            }}>
              <UserPlus size={32} color="white" />
            </div>
          </motion.div>
          <h2 style={{ marginBottom: '0.5rem', fontSize: '1.75rem' }}>Create Account</h2>
          <p style={{ color: '#94a3b8', fontSize: '0.95rem' }}>Join us to start your financial journey</p>
        </div>

        {/* Divider */}
        <div style={{
          height: '1px',
          background: 'linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.5), transparent)',
          marginBottom: '1.5rem'
        }}></div>

        <form onSubmit={handleSignup}>
          {/* Full Name Field */}
          <div className="form-group">
            <label className="label">Full Name</label>
            <div style={{ position: 'relative' }}>
              <User size={18} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8', zIndex: 1 }} />
              <input
                type="text"
                className="input-field enhanced-input"
                style={{ paddingLeft: '2.75rem' }}
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                placeholder="John Doe"
              />
            </div>
          </div>

          {/* Email Field */}
          <div className="form-group">
            <label className="label">Email</label>
            <div style={{ position: 'relative' }}>
              <Mail size={18} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8', zIndex: 1 }} />
              <input
                type="email"
                className="input-field enhanced-input"
                style={{ paddingLeft: '2.75rem' }}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="you@example.com"
              />
            </div>
          </div>

          {/* Password Field */}
          <div className="form-group">
            <label className="label">Password</label>
            <div style={{ position: 'relative' }}>
              <Lock size={18} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8', zIndex: 1 }} />
              <input
                type="password"
                className="input-field enhanced-input"
                style={{ paddingLeft: '2.75rem' }}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="••••••••"
              />
            </div>
          </div>

          {/* Confirm Password Field */}
          <div className="form-group">
            <label className="label">Confirm Password</label>
            <div style={{ position: 'relative' }}>
              <Lock size={18} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8', zIndex: 1 }} />
              <input
                type="password"
                className="input-field enhanced-input"
                style={{ paddingLeft: '2.75rem' }}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                placeholder="••••••••"
              />
            </div>
          </div>

          {/* Sign Up Button */}
          <button type="submit" className="btn-primary" style={{ width: '100%', marginTop: '0.5rem' }}>
            <span>Sign Up</span>
            <ArrowRight size={18} />
          </button>

          {/* Divider */}
          <div style={{ display: 'flex', alignItems: 'center', margin: '1.75rem 0 1.25rem' }}>
            <div style={{ flex: 1, height: '1px', background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.15))' }}></div>
            <span style={{ padding: '0 1rem', color: '#94a3b8', fontSize: '0.875rem', fontWeight: 500 }}>Or continue with</span>
            <div style={{ flex: 1, height: '1px', background: 'linear-gradient(90deg, rgba(255, 255, 255, 0.15), transparent)' }}></div>
          </div>

          {/* Google Sign Up Button */}
          <a
            href="http://localhost:8000/auth/google/login"
            className="google-btn"
            style={{
              width: '100%',
              background: 'rgba(255, 255, 255, 0.95)',
              color: '#1f2937',
              padding: '0.875rem 1.75rem',
              borderRadius: '0.75rem',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '1rem',
              transition: 'all 0.3s ease',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              textDecoration: 'none',
              boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
            }}>
            <svg style={{ width: '20px', height: '20px' }} viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            <span>Sign up with Google</span>
          </a>

          {/* Login Link */}
          <div style={{ marginTop: '2rem', textAlign: 'center', color: '#94a3b8', fontSize: '0.9rem' }}>
            Already have an account?{' '}
            <Link href="/login" style={{
              color: 'var(--primary)',
              fontWeight: 600,
              textDecoration: 'none',
              borderBottom: '1px solid transparent',
              transition: 'border-color 0.2s'
            }}>
              Log in
            </Link>
          </div>
        </form>
      </motion.div>
    </div>
  )
}
