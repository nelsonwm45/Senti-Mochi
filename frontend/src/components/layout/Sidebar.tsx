'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard,
  MessageSquare,
  FileText,
  Newspaper,
  User,
  Settings,
  ChevronLeft,
  ChevronRight,
  LogOut,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface SidebarItem {
  icon: React.ElementType;
  label: string;
  href: string;
}

const menuItems: SidebarItem[] = [
  { icon: LayoutDashboard, label: 'Dashboardaaaaa', href: '/dashboard' },
  { icon: MessageSquare, label: 'Chat', href: '/chat' },
  { icon: Newspaper, label: 'Market News', href: '/news' },
  { icon: FileText, label: 'Documents', href: '/documents' },
  { icon: User, label: 'Profile', href: '/profile' },
  { icon: Settings, label: 'Settings', href: '/settings' },
];

interface SidebarProps {
  onCollapsedChange?: (collapsed: boolean) => void;
}

export function Sidebar({ onCollapsedChange }: SidebarProps) {
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Load collapsed state from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('sidebar-collapsed');
    if (saved !== null) {
      const collapsed = saved === 'true';
      setIsCollapsed(collapsed);
      onCollapsedChange?.(collapsed);
    }
  }, [onCollapsedChange]);

  const toggleCollapsed = () => {
    const newState = !isCollapsed;
    setIsCollapsed(newState);
    localStorage.setItem('sidebar-collapsed', String(newState));
    onCollapsedChange?.(newState);
  };

  return (
    <motion.aside
      className={cn(
        'fixed left-0 top-0 z-40 h-screen',
        'glass-sidebar flex flex-col',
        'transition-all duration-300 ease-[cubic-bezier(0.25,0.1,0.25,1.0)]'
      )}
      initial={false}
      animate={{ width: isCollapsed ? 72 : 240 }}
    >
      {/* Logo */}
      <div className="flex items-center h-16 px-4 border-b border-[var(--sidebar-border)]">
        <Link href="/dashboard" className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-primary">
            <span className="text-xl font-bold text-white">M</span>
          </div>
          <AnimatePresence>
            {!isCollapsed && (
              <motion.span
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: 'auto' }}
                exit={{ opacity: 0, width: 0 }}
                className="text-xl font-bold gradient-text overflow-hidden whitespace-nowrap"
              >
                Mochi
              </motion.span>
            )}
          </AnimatePresence>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {menuItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;

          return (
            <Link key={item.href} href={item.href}>
              <motion.div
                className={cn(
                  'glass-sidebar-item',
                  isActive && 'active',
                  isCollapsed && 'justify-center px-0'
                )}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <Icon size={20} className="shrink-0" />
                <AnimatePresence>
                  {!isCollapsed && (
                    <motion.span
                      initial={{ opacity: 0, width: 0 }}
                      animate={{ opacity: 1, width: 'auto' }}
                      exit={{ opacity: 0, width: 0 }}
                      className="overflow-hidden whitespace-nowrap"
                    >
                      {item.label}
                    </motion.span>
                  )}
                </AnimatePresence>
              </motion.div>
            </Link>
          );
        })}
      </nav>

      {/* Floating Toggle Button */}
      <button
        onClick={toggleCollapsed}
        className={cn(
          'absolute -right-3 top-1/2 -translate-y-1/2',
          'w-6 h-6 rounded-full',
          'bg-white dark:bg-slate-800',
          'border border-glass-border',
          'shadow-glass hover:shadow-glass-hover',
          'flex items-center justify-center',
          'text-accent transition-all duration-200',
          'hover:scale-110 active:scale-95',
          'z-50'
        )}
        aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {isCollapsed ? (
          <ChevronRight size={14} />
        ) : (
          <ChevronLeft size={14} />
        )}
      </button>
    </motion.aside>
  );
}

export default Sidebar;
