export interface FinancialMetric {
	label: string;
	value: number;
	unit: string; // e.g., 'B', 'M', '%'
	displayValue: string; // e.g., 'RM 15B', '16.40%'
}

export interface Company {
	ticker: string;
	name: string;
	sector: string;
	marketCap: string;
	logo: string; // Using a placeholder color or initial
	description: string;
	financials: {
		incomeStatement: {
			revenue: FinancialMetric;
			netProfit: FinancialMetric;
			netMargin: FinancialMetric;
		};
		balanceSheet: {
			totalAssets: FinancialMetric;
			totalLiabilities: FinancialMetric;
			roe: FinancialMetric;
			debtToEquity: FinancialMetric;
		};
		cashFlow: {
			operatingCf: FinancialMetric;
			investingCf: FinancialMetric;
			financingCf: FinancialMetric;
		};
		quarter: string; // e.g., 'Q1 2024'
	};
}

export const mockCompanies: Company[] = [
	{
		ticker: 'MAYBANK',
		name: 'Malayan Banking Bhd',
		sector: 'Financial Services',
		marketCap: '110.2B',
		logo: 'bg-yellow-500',
		description: 'Malayan Banking Berhad is a handsome bank.',
		financials: {
			incomeStatement: {
				revenue: { label: 'Revenue', value: 15000000000, unit: 'B', displayValue: 'RM 15B' },
				netProfit: { label: 'Net Profit', value: 2500000000, unit: 'B', displayValue: 'RM 2.5B' },
				netMargin: { label: 'Net Margin', value: 16.4, unit: '%', displayValue: '16.40%' },
			},
			balanceSheet: {
				totalAssets: { label: 'Total Assets', value: 950000000000, unit: 'B', displayValue: 'RM 950B' },
				totalLiabilities: { label: 'Total Liabilities', value: 860000000000, unit: 'B', displayValue: 'RM 860B' },
				roe: { label: 'ROE', value: 10.5, unit: '%', displayValue: '10.50%' },
				debtToEquity: { label: 'Debt/Equity', value: 0.8, unit: '', displayValue: '0.8' },
			},
			cashFlow: {
				operatingCf: { label: 'Operating CF', value: 3200000000, unit: 'B', displayValue: 'RM 3.2B' },
				investingCf: { label: 'Investing CF', value: -500000000, unit: 'M', displayValue: '-RM 500M' },
				financingCf: { label: 'Financing CF', value: -1200000000, unit: 'B', displayValue: '-RM 1.2B' },
			},
			quarter: 'Q1 2024',
		},
	},
	{
		ticker: 'CIMB',
		name: 'CIMB Group Holdings Bhd',
		sector: 'Financial Services',
		marketCap: '70.1B',
		logo: 'bg-red-600',
		description: 'CIMB Group Holdings Berhad is another handsome bank.',
		financials: {
			incomeStatement: {
				revenue: { label: 'Revenue', value: 12000000000, unit: 'B', displayValue: 'RM 12B' },
				netProfit: { label: 'Net Profit', value: 2000000000, unit: 'B', displayValue: 'RM 2B' },
				netMargin: { label: 'Net Margin', value: 16.1, unit: '%', displayValue: '16.10%' },
			},
			balanceSheet: {
				totalAssets: { label: 'Total Assets', value: 720000000000, unit: 'B', displayValue: 'RM 720B' },
				totalLiabilities: { label: 'Total Liabilities', value: 650000000000, unit: 'B', displayValue: 'RM 650B' },
				roe: { label: 'ROE', value: 9.8, unit: '%', displayValue: '9.80%' },
				debtToEquity: { label: 'Debt/Equity', value: 0.95, unit: '', displayValue: '0.95' },
			},
			cashFlow: {
				operatingCf: { label: 'Operating CF', value: 2100000000, unit: 'B', displayValue: 'RM 2.1B' },
				investingCf: { label: 'Investing CF', value: -350000000, unit: 'M', displayValue: '-RM 350M' },
				financingCf: { label: 'Financing CF', value: -950000000, unit: 'M', displayValue: '-RM 950M' },
			},
			quarter: 'Q1 2024',
		},
	},
	{
		ticker: 'PBBANK',
		name: 'Public Bank Bhd',
		sector: 'Financial Services',
		marketCap: '85.3B',
		logo: 'bg-red-500',
		description: 'Public Bank Berhad is a solid bank.',
		financials: {
			incomeStatement: {
				revenue: { label: 'Revenue', value: 11000000000, unit: 'B', displayValue: 'RM 11B' },
				netProfit: { label: 'Net Profit', value: 2200000000, unit: 'B', displayValue: 'RM 2.2B' },
				netMargin: { label: 'Net Margin', value: 20.0, unit: '%', displayValue: '20.00%' },
			},
			balanceSheet: {
				totalAssets: { label: 'Total Assets', value: 640000000000, unit: 'B', displayValue: 'RM 640B' },
				totalLiabilities: { label: 'Total Liabilities', value: 580000000000, unit: 'B', displayValue: 'RM 580B' },
				roe: { label: 'ROE', value: 12.5, unit: '%', displayValue: '12.50%' },
				debtToEquity: { label: 'Debt/Equity', value: 0.5, unit: '', displayValue: '0.50' },
			},
			cashFlow: {
				operatingCf: { label: 'Operating CF', value: 2800000000, unit: 'B', displayValue: 'RM 2.8B' },
				investingCf: { label: 'Investing CF', value: -200000000, unit: 'M', displayValue: '-RM 200M' },
				financingCf: { label: 'Financing CF', value: -1000000000, unit: 'B', displayValue: '-RM 1.0B' },
			},
			quarter: 'Q1 2024',
		},
	},
	{
		ticker: 'TENAGA',
		name: 'Tenaga Nasional Bhd',
		sector: 'Utilities',
		marketCap: '55.0B',
		logo: 'bg-blue-600',
		description: 'Tenaga Nasional is the power.',
		financials: {
			incomeStatement: {
				revenue: { label: 'Revenue', value: 18000000000, unit: 'B', displayValue: 'RM 18B' },
				netProfit: { label: 'Net Profit', value: 1500000000, unit: 'B', displayValue: 'RM 1.5B' },
				netMargin: { label: 'Net Margin', value: 8.3, unit: '%', displayValue: '8.30%' },
			},
			balanceSheet: {
				totalAssets: { label: 'Total Assets', value: 150000000000, unit: 'B', displayValue: 'RM 150B' },
				totalLiabilities: { label: 'Total Liabilities', value: 100000000000, unit: 'B', displayValue: 'RM 100B' },
				roe: { label: 'ROE', value: 7.2, unit: '%', displayValue: '7.20%' },
				debtToEquity: { label: 'Debt/Equity', value: 1.8, unit: '', displayValue: '1.80' },
			},
			cashFlow: {
				operatingCf: { label: 'Operating CF', value: 5000000000, unit: 'B', displayValue: 'RM 5.0B' },
				investingCf: { label: 'Investing CF', value: -4000000000, unit: 'B', displayValue: '-RM 4.0B' },
				financingCf: { label: 'Financing CF', value: -500000000, unit: 'M', displayValue: '-RM 500M' },
			},
			quarter: 'Q1 2024',
		},
	},
];
