'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { getToken, removeToken } from '@/lib/auth';
import apiClient from '@/lib/apiClient';

interface User {
  id: string;
  email: string;
  full_name?: string;
  role: 'USER' | 'ADMIN' | 'AUDITOR' | 'RM' | 'ANALYST' | 'RISK';
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  isLoading: true,
  logout: () => {},
  refreshUser: async () => {},
});

export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  const fetchUser = async () => {
    try {
      const token = getToken();
      if (!token) {
        throw new Error('No token');
      }
      const { data } = await apiClient.get<User>('/users/me');
      setUser(data);
    } catch {
      setUser(null);
      // Optional: removeToken() if check fails? 
      // Sometimes we just want to know we aren't logged in.
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUser();
  }, []);

  const logout = () => {
    removeToken();
    setUser(null);
    router.push('/login');
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, logout, refreshUser: fetchUser }}>
      {children}
    </AuthContext.Provider>
  );
}
