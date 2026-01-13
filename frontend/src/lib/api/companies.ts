import apiClient from '../apiClient';

export interface Company {
	id: string;
	ticker: string;
	name: string;
	sector: string;
	sub_sector?: string;
}

export const companiesApi = {
	/**
	 * Search companies by query
	 */
	async search(query?: string): Promise<Company[]> {
		const params = query ? { query } : {};
		const { data } = await apiClient.get<Company[]>('/api/v1/companies/search', {
			params,
		});
		return data;
	},

	/**
	 * Get company details
	 */
	async get(ticker: string): Promise<Company> {
		const { data } = await apiClient.get<Company>(`/api/v1/companies/${ticker}`);
		return data;
	}
};
