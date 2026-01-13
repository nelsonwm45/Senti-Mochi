export interface BursaCompany {
	ticker: string;
	name: string;
	sector: string;
}

export const bursaCompanies: BursaCompany[] = [
	{ ticker: '1155.KL', name: 'Malayan Banking Berhad (Maybank)', sector: 'Financial Services' },
	{ ticker: '1295.KL', name: 'Public Bank Berhad', sector: 'Financial Services' },
	{ ticker: '1023.KL', name: 'CIMB Group Holdings Berhad', sector: 'Financial Services' },
	{ ticker: '5347.KL', name: 'Tenaga Nasional Berhad', sector: 'Utilities' },
	{ ticker: '5183.KL', name: 'Petronas Chemicals Group Berhad', sector: 'Industrial Products & Services' },
	{ ticker: '5225.KL', name: 'IHH Healthcare Berhad', sector: 'Health Care' },
	{ ticker: '6947.KL', name: 'CelcomDigi Berhad', sector: 'Telecommunications & Media' },
	{ ticker: '5819.KL', name: 'Hong Leong Bank Berhad', sector: 'Financial Services' },
	{ ticker: '8869.KL', name: 'Press Metal Aluminium Holdings Berhad', sector: 'Industrial Products & Services' },
	{ ticker: '3816.KL', name: 'MISC Berhad', sector: 'Transportation & Logistics' },
	{ ticker: '1961.KL', name: 'IOI Corporation Berhad', sector: 'Plantation' },
	{ ticker: '4197.KL', name: 'Sime Darby Berhad', sector: 'Consumer Products & Services' },
	{ ticker: '6012.KL', name: 'Maxis Berhad', sector: 'Telecommunications & Media' },
	{ ticker: '1066.KL', name: 'RHB Bank Berhad', sector: 'Financial Services' },
	{ ticker: '3182.KL', name: 'Genting Berhad', sector: 'Consumer Products & Services' },
	{ ticker: '4715.KL', name: 'Genting Malaysia Berhad', sector: 'Consumer Products & Services' },
	{ ticker: '1015.KL', name: 'AMMB Holdings Berhad', sector: 'Financial Services' },
	{ ticker: '7277.KL', name: 'Dialog Group Berhad', sector: 'Energy' },
	{ ticker: '5398.KL', name: 'Gamuda Berhad', sector: 'Construction' },
	{ ticker: '4707.KL', name: 'Nestle (Malaysia) Berhad', sector: 'Consumer Products & Services' },
	{ ticker: '2445.KL', name: 'Kuala Lumpur Kepong Berhad', sector: 'Plantation' },
	{ ticker: '4065.KL', name: 'PPB Group Berhad', sector: 'Consumer Products & Services' },
	{ ticker: '6033.KL', name: 'Petronas Gas Berhad', sector: 'Utilities' },
	{ ticker: '5014.KL', name: 'Malaysia Airports Holdings Berhad', sector: 'Transportation & Logistics' },
	{ ticker: '4863.KL', name: 'Telekom Malaysia Berhad', sector: 'Telecommunications & Media' },
	{ ticker: '7084.KL', name: 'QL Resources Berhad', sector: 'Consumer Products & Services' },
	{ ticker: '5296.KL', name: 'MR D.I.Y. Group (M) Berhad', sector: 'Consumer Products & Services' },
	{ ticker: '4677.KL', name: 'YTL Corporation Berhad', sector: 'Utilities' },
	{ ticker: '6742.KL', name: 'YTL Power International Berhad', sector: 'Utilities' },
	{ ticker: '0166.KL', name: 'Inari Amertron Berhad', sector: 'Technology' }
];

// Helper to filter companies
export const searchBursaCompanies = (query: string) => {
	const lowerQuery = query.toLowerCase();
	return bursaCompanies.filter(c =>
		c.name.toLowerCase().includes(lowerQuery) ||
		c.ticker.toLowerCase().includes(lowerQuery)
	);
};
