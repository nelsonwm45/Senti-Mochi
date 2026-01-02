'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Home, User, LogOut, LogIn } from 'lucide-react';

export default function Navbar() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('token');
    setIsLoggedIn(!!token);

    const handleStorageChange = () => {
        setIsLoggedIn(!!localStorage.getItem('token'));
    };
    
    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('auth-change', handleStorageChange);

    return () => {
        window.removeEventListener('storage', handleStorageChange);
        window.removeEventListener('auth-change', handleStorageChange);
    };
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsLoggedIn(false);
    window.dispatchEvent(new Event('auth-change'));
    router.push('/login');
  };

  return (
    <motion.nav 
      className="navbar"
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ type: 'spring', stiffness: 100, damping: 20 }}
    >
      <div className="container navbar-content">
        <Link href="/" className="nav-brand">FinanceAI</Link>
        <div className="nav-links">
          <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Home size={18} /> <span className="hide-mobile">Home</span>
          </Link>
          {isLoggedIn ? (
            <>
              <Link href="/profile" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <User size={18} /> <span className="hide-mobile">Profile</span>
              </Link>
              <button 
                onClick={handleLogout} 
                className="btn-primary" 
                style={{ padding: '0.5rem 1rem', background: 'rgba(255,255,255,0.1)', border: '1px solid var(--glass-border)', boxShadow: 'none' }}
              >
                <LogOut size={16} /> Logout
              </button>
            </>
          ) : (
            <Link href="/login" className="btn-primary" style={{ padding: '0.5rem 1rem' }}>
              <LogIn size={16} /> Login
            </Link>
          )}
        </div>
      </div>
    </motion.nav>
  );
}
