import apiClient from '../apiClient';

export interface User {
	id: string;
	email: string;
	full_name?: string;
	role: 'USER' | 'ADMIN' | 'AUDITOR' | 'RM' | 'ANALYST' | 'RISK';
	is_active: boolean;
	created_at: string;
}

export const adminApi = {
	getUsers: async () => {
		const { data } = await apiClient.get<User[]>('/users/admin/users');
		return data;
	},
};
