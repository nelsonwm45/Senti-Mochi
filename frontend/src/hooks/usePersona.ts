'use client';

import { useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getToken } from '@/lib/auth';
import api from '@/lib/apiClient';
import { AnalysisPersona } from '@/types/persona';

export interface UserWithPersona {
    id: string;
    email: string;
    full_name?: string;
    name?: string;
    avatar_url?: string;
    analysis_persona?: AnalysisPersona;
    persona?: AnalysisPersona;
    created_at: string;
}

async function fetchUserPersona(): Promise<UserWithPersona> {
    const response = await api.get('/api/v1/users/me');
    console.log('[usePersona] Fetched user data:', response.data);
    return response.data;
}

async function updateUserPersona(newPersona: AnalysisPersona): Promise<UserWithPersona> {
    const response = await api.patch('/api/v1/users/me/persona', { analysis_persona: newPersona });
    console.log('[usePersona] Updated persona:', response.data);
    return response.data;
}

export function usePersona() {
    const token = getToken();
    const queryClient = useQueryClient();

    const {
        data: userPersona,
        isLoading,
        error,
        refetch,
    } = useQuery({
        queryKey: ['user', 'persona'],
        queryFn: fetchUserPersona,
        enabled: !!token,
        staleTime: 0, // Always refetch when component mounts
        retry: 1,
    });

    const updatePersonaMutation = useMutation({
        mutationFn: updateUserPersona,
        onSuccess: (data) => {
            queryClient.setQueryData(['user', 'persona'], data);
        },
    });

    // Refetch persona when page becomes visible (user returns to tab/window)
    useEffect(() => {
        const handleVisibilityChange = () => {
            if (!document.hidden) {
                refetch();
            }
        };

        document.addEventListener('visibilitychange', handleVisibilityChange);
        return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
    }, [refetch]);

    return {
        user: userPersona,
        persona: userPersona?.analysis_persona || userPersona?.persona || 'RELATIONSHIP_MANAGER',
        isLoading,
        error,
        refetch,
        updatePersona: (persona: AnalysisPersona) => updatePersonaMutation.mutateAsync(persona),
        isUpdating: updatePersonaMutation.isPending,
        isAuthenticated: !!token && !!userPersona,
    };
}

export default usePersona;
