'use client';

import { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { Sidebar } from './Sidebar';
import { Navbar } from './Navbar';

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const handleCollapsedChange = useCallback((collapsed: boolean) => {
    setSidebarCollapsed(collapsed);
  }, []);

  return (
    <div className="min-h-screen bg-background">
      {/* Animated background */}
      <div className="animated-bg" />

      {/* Sidebar */}
      <Sidebar onCollapsedChange={handleCollapsedChange} />

      {/* Navbar */}
      <Navbar sidebarCollapsed={sidebarCollapsed} />

      {/* Main content */}
      <motion.main
        className={cn(
          'pt-16 min-h-screen',
          'transition-all duration-300 ease-out'
        )}
        style={{
          marginLeft: sidebarCollapsed ? 72 : 240,
        }}
        initial={false}
        animate={{
          marginLeft: sidebarCollapsed ? 72 : 240,
        }}
      >
        <div className="p-6">
          {children}
        </div>
      </motion.main>
    </div>
  );
}

export default AppLayout;
