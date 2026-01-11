'use client';

import { useQuery } from '@tanstack/react-query';
import { getToken } from '@/lib/auth';
import api from '@/lib/apiClient';

export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  created_at: string;
}

async function fetchCurrentUser(): Promise<User> {
  const response = await api.get('/users/me');
  return response.data;
}

export function useUser() {
  const token = getToken();

  const {
    data: user,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['user', 'me'],
    queryFn: fetchCurrentUser,
    enabled: !!token,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });

  return {
    user,
    isLoading,
    error,
    refetch,
    isAuthenticated: !!token && !!user,
  };
}

export default useUser;
