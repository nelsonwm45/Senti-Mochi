'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, LogOut, User, Settings, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Breadcrumbs } from './Breadcrumbs';
import { useAuth } from '@/lib/auth';
import { useUser } from '@/hooks/useUser';

interface NavbarProps {
  sidebarCollapsed?: boolean;
}

export function Navbar({ sidebarCollapsed = false }: NavbarProps) {
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);
  const { logout } = useAuth();
  const { user } = useUser();

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(event.target as Node)) {
        setIsProfileOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    logout();
  };

  return (
    <header
      className={cn(
        'fixed top-0 right-0 z-30 h-16',
        'glass-navbar',
        'transition-all duration-300 ease-out'
      )}
      style={{
        left: sidebarCollapsed ? 72 : 240,
      }}
    >
      <div className="flex items-center justify-between h-full px-6">
        {/* Breadcrumbs */}
        <Breadcrumbs />

        {/* Right side actions */}
        <div className="flex items-center gap-3">
          {/* Notifications */}
          <motion.button
            className={cn(
              'relative flex items-center justify-center w-10 h-10 rounded-xl',
              'bg-glass-bg backdrop-blur-glass border border-glass-border',
              'text-foreground-secondary hover:text-accent',
              'transition-colors duration-200'
            )}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            aria-label="Notifications"
          >
            <Bell size={20} />
            {/* Notification dot */}
            <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full" />
          </motion.button>

          {/* Profile Dropdown */}
          <div className="relative" ref={profileRef}>
            <motion.button
              onClick={() => setIsProfileOpen(!isProfileOpen)}
              className={cn(
                'flex items-center gap-2 px-3 py-2 rounded-xl',
                'bg-glass-bg backdrop-blur-glass border border-glass-border',
                'hover:border-accent/30',
                'transition-colors duration-200'
              )}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-primary">
                <span className="text-sm font-semibold text-white">
                  {user?.name?.charAt(0).toUpperCase() || 'U'}
                </span>
              </div>
              <span className="text-sm font-medium text-foreground hidden sm:block">
                {user?.name || 'User'}
              </span>
              <ChevronDown
                size={16}
                className={cn(
                  'text-foreground-muted transition-transform duration-200',
                  isProfileOpen && 'rotate-180'
                )}
              />
            </motion.button>

            <AnimatePresence>
              {isProfileOpen && (
                <motion.div
                  initial={{ opacity: 0, y: 10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 10, scale: 0.95 }}
                  transition={{ duration: 0.15 }}
                  className={cn(
                    'absolute right-0 mt-2 w-56',
                    'bg-glass-bg backdrop-blur-xl',
                    'border border-glass-border rounded-xl',
                    'shadow-glass-hover',
                    'overflow-hidden'
                  )}
                >
                  {/* User info */}
                  <div className="px-4 py-3 border-b border-glass-border">
                    <p className="text-sm font-medium text-foreground">{user?.name || 'User'}</p>
                    <p className="text-xs text-foreground-muted truncate">{user?.email || 'user@example.com'}</p>
                  </div>

                  {/* Menu items */}
                  <div className="py-1">
                    <Link
                      href="/profile"
                      onClick={() => setIsProfileOpen(false)}
                      className="flex items-center gap-3 px-4 py-2 text-sm text-foreground-secondary hover:bg-accent/10 hover:text-accent transition-colors"
                    >
                      <User size={16} />
                      Profile
                    </Link>
                    <Link
                      href="/settings"
                      onClick={() => setIsProfileOpen(false)}
                      className="flex items-center gap-3 px-4 py-2 text-sm text-foreground-secondary hover:bg-accent/10 hover:text-accent transition-colors"
                    >
                      <Settings size={16} />
                      Settings
                    </Link>
                  </div>

                  {/* Logout */}
                  <div className="py-1 border-t border-glass-border">
                    <button
                      onClick={handleLogout}
                      className="flex items-center gap-3 w-full px-4 py-2 text-sm text-red-500 hover:bg-red-500/10 transition-colors"
                    >
                      <LogOut size={16} />
                      Log out
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Navbar;
