'use client';

import ProtectedLayout from '@/components/layouts/ProtectedLayout';
import { useTheme } from 'next-themes';
import { Moon, Sun, Monitor, User, Settings as SettingsIcon } from 'lucide-react';
import { useEffect, useState } from 'react';

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // Prevent hydration mismatch
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  return (
    <ProtectedLayout>
      <div className="min-h-full bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="flex items-center space-x-3 mb-8">
            <div className="p-3 bg-gradient-to-br from-gray-500 to-gray-600 rounded-xl">
              <SettingsIcon className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                Settings
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                Manage your preferences and account settings
              </p>
            </div>
          </div>

          <div className="space-y-6">
            {/* Appearance Section */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
                  <Monitor className="w-5 h-5 mr-2" />
                  Appearance
                </h2>
              </div>
              <div className="p-6">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
                  Theme Preference
                </label>
                <div className="grid grid-cols-3 gap-4">
                  <button
                    onClick={() => setTheme('light')}
                    className={`flex flex-col items-center justify-center p-4 rounded-lg border-2 transition-all ${
                      theme === 'light'
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 text-gray-600 dark:text-gray-400'
                    }`}
                  >
                    <Sun className="w-6 h-6 mb-2" />
                    <span className="block text-sm font-medium">Light</span>
                  </button>
                  <button
                    onClick={() => setTheme('dark')}
                    className={`flex flex-col items-center justify-center p-4 rounded-lg border-2 transition-all ${
                      theme === 'dark'
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 text-gray-600 dark:text-gray-400'
                    }`}
                  >
                    <Moon className="w-6 h-6 mb-2" />
                    <span className="block text-sm font-medium">Dark</span>
                  </button>
                  <button
                    onClick={() => setTheme('system')}
                    className={`flex flex-col items-center justify-center p-4 rounded-lg border-2 transition-all ${
                      theme === 'system'
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 text-gray-600 dark:text-gray-400'
                    }`}
                  >
                    <Monitor className="w-6 h-6 mb-2" />
                    <span className="block text-sm font-medium">System</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Profile Placeholder */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden opacity-75">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
                  <User className="w-5 h-5 mr-2" />
                  Profile Settings
                </h2>
              </div>
              <div className="p-6">
                <p className="text-gray-500 dark:text-gray-400 italic">
                  Profile management features coming soon in Phase 3.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </ProtectedLayout>
  );
}
