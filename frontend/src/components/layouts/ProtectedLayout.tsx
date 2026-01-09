'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/navigation/Sidebar';
import { getToken } from '@/lib/auth';

export default function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.push('/login');
    } else {
      setIsAuthenticated(true);
    }
  }, [router]);

  if (!isAuthenticated) {
    return null; // Or a loading spinner
  }

  return (
    <div className="flex h-screen overflow-hidden bg-gray-900 text-white">
      <Sidebar />
      <main className="flex-1 overflow-auto bg-gradient-to-br from-gray-900 to-gray-800">
        {children}
      </main>
    </div>
  );
}
