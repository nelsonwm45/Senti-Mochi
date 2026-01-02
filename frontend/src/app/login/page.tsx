'use client';
import { useState } from 'react';
import axios from 'axios';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Mail, Lock, LogIn, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);
      
      const res = await axios.post('http://localhost:8000/auth/token', formData);
      localStorage.setItem('token', res.data.access_token);
      window.dispatchEvent(new Event('auth-change'));
      router.push('/profile');
    } catch (err) {
      alert('Login failed');
    }
  };

  return (
    <div className="container page-center">
      <motion.div 
        className="glass-card" 
        style={{ width: '100%', maxWidth: '400px' }}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h2 style={{ marginBottom: '0.5rem' }}>Welcome Back</h2>
          <p style={{ color: '#94a3b8' }}>Enter your credentials to access your account</p>
        </div>

        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label className="label">Email</label>
            <div style={{ position: 'relative' }}>
              <Mail size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
              <input 
                type="email" 
                className="input-field" 
                style={{ paddingLeft: '2.5rem' }}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="you@example.com"
              />
            </div>
          </div>
          <div className="form-group">
            <label className="label">Password</label>
            <div style={{ position: 'relative' }}>
              <Lock size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
              <input 
                type="password" 
                className="input-field" 
                style={{ paddingLeft: '2.5rem' }}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="••••••••"
              />
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', margin: '1.5rem 0' }}>
            <div style={{ flex: 1, height: '1px', background: 'var(--glass-border)' }}></div>
            <span style={{ padding: '0 0.75rem', color: '#94a3b8', fontSize: '0.875rem' }}>Or continue with</span>
            <div style={{ flex: 1, height: '1px', background: 'var(--glass-border)' }}></div>
          </div>

          <a 
            href="http://localhost:8000/auth/google/login"
            className="btn-primary" 
            style={{ 
              width: '100%', 
              background: 'white', 
              color: 'black', 
              boxShadow: 'none',
              display: 'flex',
              justifyContent: 'center',
              textDecoration: 'none' 
            }}>
             {/* Simple Google G Icon */}
            <svg style={{  width: '20px', height: '20px', marginRight: '0.5rem' }} viewBox="0 0 24 24">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            Sign in with Google
          </a> 
          
          <button type="submit" className="btn-primary" style={{ width: '100%', marginTop: '1rem' }}>
            Login <ArrowRight size={18} />
          </button>
          
          <div style={{ marginTop: '1.5rem', textAlign: 'center', color: '#94a3b8', fontSize: '0.9rem' }}>
            Don't have an account?{' '}
            <Link href="/signup" style={{ color: 'var(--primary)', fontWeight: 600 }}>
              Sign up
            </Link>
          </div>
        </form>
      </motion.div>
    </div>
  )
}
