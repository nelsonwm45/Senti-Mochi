'use client';

import { useRouter } from 'next/navigation';

export const AUTH_TOKEN_KEY = 'token';

export const getToken = (): string | null => {
	if (typeof window !== 'undefined') {
		return localStorage.getItem(AUTH_TOKEN_KEY);
	}
	return null;
};

export const setToken = (token: string) => {
	if (typeof window !== 'undefined') {
		localStorage.setItem(AUTH_TOKEN_KEY, token);
		window.dispatchEvent(new Event('auth-change'));
	}
};

export const removeToken = () => {
	if (typeof window !== 'undefined') {
		localStorage.removeItem(AUTH_TOKEN_KEY);
		window.dispatchEvent(new Event('auth-change'));
	}
};

export const isAuthenticated = (): boolean => {
	return !!getToken();
};

export function useAuth() {
	const router = useRouter();

	const logout = () => {
		removeToken();
		router.push('/login');
	};

	return {
		getToken,
		setToken,
		removeToken,
		isAuthenticated,
		logout
	};
}
