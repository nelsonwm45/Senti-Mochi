'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  FileText,
  MessageCircle,
  User,
  LogOut,
  Menu,
  X,
  Settings,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '@/lib/auth';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Documents', href: '/documents', icon: FileText },
  { name: 'Chat', href: '/chat', icon: MessageCircle },
  { name: 'Settings', href: '/settings', icon: Settings },
  { name: 'Profile', href: '/profile', icon: User },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const { logout } = useAuth();

  return (
    <>
      {/* Mobile menu button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg"
      >
        {isOpen ? (
          <X className="w-6 h-6 text-gray-600 dark:text-gray-300" />
        ) : (
          <Menu className="w-6 h-6 text-gray-600 dark:text-gray-300" />
        )}
      </button>

      {/* Backdrop for mobile */}
      {isOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={`
          fixed lg:static inset-y-0 left-0 z-40
          ${isCollapsed ? 'w-20' : 'w-64'}
          bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700
          transform transition-all duration-300 ease-in-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          flex flex-col
        `}
      >
        <div className="flex flex-col h-full relative">
          {/* Toggle Button (Desktop only) */}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="hidden lg:flex absolute -right-3 top-20 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-full p-1 shadow-md hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors z-50"
          >
            {isCollapsed ? (
              <ChevronRight className="w-4 h-4 text-gray-600 dark:text-gray-300" />
            ) : (
              <ChevronLeft className="w-4 h-4 text-gray-600 dark:text-gray-300" />
            )}
          </button>

          {/* Logo */}
          <div className={`flex items-center h-16 px-4 border-b border-gray-200 dark:border-gray-700 ${isCollapsed ? 'justify-center' : 'px-6'}`}>
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center flex-shrink-0">
                <span className="text-white font-bold text-sm">MF</span>
              </div>
              {!isCollapsed && (
                <span className="text-lg font-bold text-gray-900 dark:text-white whitespace-nowrap overflow-hidden transition-opacity duration-300">
                  Mochi Finance
                </span>
              )}
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
            {navigation.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  onClick={() => setIsOpen(false)}
                  className={`
                    flex items-center px-3 py-2.5 rounded-lg transition-colors group relative
                    ${
                      isActive
                        ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }
                    ${isCollapsed ? 'justify-center' : ''}
                  `}
                  title={isCollapsed ? item.name : ''}
                >
                  <item.icon className={`w-5 h-5 flex-shrink-0 ${!isCollapsed && 'mr-3'}`} />
                  {!isCollapsed && (
                    <span className="font-medium whitespace-nowrap overflow-hidden">{item.name}</span>
                  )}
                  {/* Tooltip for collapsed state */}
                  {isCollapsed && (
                    <div className="absolute left-full ml-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
                      {item.name}
                    </div>
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Logout */}
          <div className="p-3 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={logout}
              className={`
                w-full flex items-center px-3 py-2.5 rounded-lg text-red-600 dark:text-red-400 
                hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors group relative
                ${isCollapsed ? 'justify-center' : ''}
              `}
              title={isCollapsed ? 'Logout' : ''}
            >
              <LogOut className={`w-5 h-5 flex-shrink-0 ${!isCollapsed && 'mr-3'}`} />
              {!isCollapsed && <span className="font-medium whitespace-nowrap overflow-hidden">Logout</span>}
              
              {isCollapsed && (
                <div className="absolute left-full ml-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
                  Logout
                </div>
              )}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
