import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = typeof window === 'undefined'
	? (process.env.INTERNAL_API_URL || 'http://finance_backend:8000') // Server-side
	: ''; // Client-side (relative path to use proxy)

import { getToken, removeToken } from './auth';

// Create axios instance with default config
const apiClient: AxiosInstance = axios.create({
	baseURL: API_BASE_URL,
	headers: {
		'Content-Type': 'application/json',
	},
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
	(config) => {
		const token = getToken();
		if (token) {
			config.headers.Authorization = `Bearer ${token}`;
		}
		return config;
	},
	(error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
	(response) => response,
	(error) => {
		if (error.response?.status === 401) {
			// Redirect to login if unauthorized
			removeToken();
			if (typeof window !== 'undefined') {
				window.location.href = '/login';
			}
		}
		return Promise.reject(error);
	}
);

export default apiClient;
