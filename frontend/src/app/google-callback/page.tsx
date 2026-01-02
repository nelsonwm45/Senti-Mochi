'use client';
import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';

export default function GoogleCallback() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const token = searchParams.get('token');
    if (token) {
      localStorage.setItem('token', token);
      window.dispatchEvent(new Event('auth-change'));
      router.push('/profile');
    } else {
      setTimeout(() => {
          router.push('/login');
      }, 2000);
    }
  }, [router, searchParams]);

  return (
    <div className="container page-center">
      <motion.div 
        className="glass-card" 
        style={{ textAlign: 'center' }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <h2>Authenticating...</h2>
        <p style={{ color: '#94a3b8' }}>Please wait while we log you in.</p>
        <div style={{ marginTop: '1rem' }} className="animate-float">
             Please wait...
        </div>
      </motion.div>
    </div>
  );
}
