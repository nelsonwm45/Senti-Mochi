'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { Mail, Lock, LogIn, ArrowRight, AlertCircle } from 'lucide-react';
import Link from 'next/link';

import { setToken, getToken } from '@/lib/auth';
import { GlassCard } from '@/components/ui/GlassCard';
import { GlassInput } from '@/components/ui/GlassInput';
import { GlassButton } from '@/components/ui/GlassButton';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  // Redirect if already logged in
  useEffect(() => {
    const token = getToken();
    if (token) {
      router.push('/dashboard');
    }
  }, [router]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);
      
      const res = await axios.post('http://localhost:8000/auth/token', formData);
      setToken(res.data.access_token);
      
      // Use window.location to force a full refresh and update auth state in Sidebar
      window.location.href = '/dashboard';
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 401) {
          // Expected error for invalid credentials
          setError('Invalid email or password. Please try again.');
      } else {
          // Unexpected errors
          console.error(err);
          setError('Something went wrong. Please try again later.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md">
      <GlassCard className="p-8">
        {/* Header Section */}
        <div className="text-center mb-8">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="w-16 h-16 mx-auto mb-4 bg-gradient-brand rounded-2xl flex items-center justify-center shadow-lg shadow-accent/20"
          >
            <LogIn className="w-8 h-8 text-white" />
          </motion.div>
          <h2 className="text-2xl font-bold text-foreground mb-2">Welcome Back</h2>
          <p className="text-foreground-muted">Enter your credentials to access your account</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 flex items-center gap-3 text-red-500 text-sm"
              >
                <AlertCircle size={18} />
                <p>{error}</p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Email Field */}
          <GlassInput
            label="Email"
            leftIcon={<Mail size={18} />}
            type="email"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              if (error) setError('');
            }}
            required
            placeholder="you@example.com"
          />

          {/* Password Field */}
          <GlassInput
            label="Password"
            leftIcon={<Lock size={18} />}
            type="password"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              if (error) setError('');
            }}
            required
            placeholder="••••••••"
          />

          {/* Login Button */}
          <GlassButton
            type="submit"
            variant="primary"
            size="lg"
            className="w-full justify-center"
            disabled={isLoading}
            rightIcon={<ArrowRight size={20} />}
          >
            {isLoading ? 'Logging in...' : 'Login'}
          </GlassButton>
        </form>

        {/* Divider */}
        <div className="my-8 flex items-center">
          <div className="flex-1 h-px bg-glass-border"></div>
          <span className="px-4 text-sm text-foreground-muted font-medium">Or continue with</span>
          <div className="flex-1 h-px bg-glass-border"></div>
        </div>

        {/* Google Sign In Button */}
        <a
          href="http://localhost:8000/auth/google/login"
          className="w-full block"
        >
          <GlassButton variant="outline" size="lg" className="w-full justify-center gap-2">
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            Sign in with Google
          </GlassButton>
        </a>

        {/* Sign Up Link */}
        <div className="mt-8 text-center text-sm text-foreground-muted">
          Don't have an account?{' '}
          <Link href="/signup" className="text-accent font-semibold hover:text-accent-light transition-colors">
            Sign up
          </Link>
        </div>
      </GlassCard>
    </div>
  );
}
