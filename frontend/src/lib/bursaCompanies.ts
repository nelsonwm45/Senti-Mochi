export interface BursaCompany {
	ticker: string;
	name: string;
	sector: string;
}

/**
 * @deprecated Use API search instead.
 */
export const bursaCompanies: BursaCompany[] = [];

/**
 * @deprecated Use API search instead.
 */
export const searchBursaCompanies = (query: string) => {
	return [];
};
