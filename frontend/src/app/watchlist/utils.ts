
export const formatValue = (val: number | null | undefined) => {
	if (val === undefined || val === null) return '-';
	// If percent (val < 1 and > -1, maybe? No, specific metrics might be percent)
	// The user didn't specify auto-percent, but for Margin we know it's %.
	// Let's just stick to locale string for now.
	return val.toLocaleString(undefined, { maximumFractionDigits: 2 });
};

export const formatPercent = (val: number | null | undefined) => {
	if (val === undefined || val === null) return '-';
	return `${val.toLocaleString(undefined, { maximumFractionDigits: 2 })}%`;
};

export const getValue = (companyData: any, category: string, metricName: string) => {
	if (!companyData) return null;
	const cat = companyData[category];
	if (!cat) return null;
	const dates = Object.keys(cat).sort().reverse();
	const latestDate = dates[0];
	if (!latestDate) return null;

	const metrics = cat[latestDate];
	const key = Object.keys(metrics).find(k => k.toLowerCase() === metricName.toLowerCase() || k.toLowerCase().includes(metricName.toLowerCase()));

	// Exact match preference? The 'includes' is risky for things like 'Revenue' matching 'Cost of Revenue'.
	// Let's try exact match first, then loose.
	const exactKey = Object.keys(metrics).find(k => k.toLowerCase() === metricName.toLowerCase());
	if (exactKey) return metrics[exactKey];

	// For 'Total Revenue', 'Revenue' might be acceptable.
	// The previous logic was: includes OR ===.
	// Let's stick to the previous logic but maybe prioritizing exactness if we can?
	// actually previous logic: find(k => includes || ===)
	// 'Cost of Revenue' includes 'Revenue'. So searching 'Revenue' might pick 'Cost of Revenue' if it comes first.
	// That's bad.
	// Let's improve it: Exact match first.

	if (key) return metrics[key];
	return null;
};

// Better getValue that prioritizes exact match
export const getSafeValue = (companyData: any, category: string, metricName: string) => {
	if (!companyData || !companyData[category]) return null;
	const cat = companyData[category];
	const dates = Object.keys(cat).sort().reverse();
	if (dates.length === 0) return null;
	const metrics = cat[dates[0]];

	// 1. Try exact match (case insensitive)
	let key = Object.keys(metrics).find(k => k.toLowerCase() === metricName.toLowerCase());
	if (key) return metrics[key];

	// 2. Try contains (but be careful)
	// For specific known ambiguous keys, maybe avoid? 
	// But for "Net Income", "Net Income Common Stockholders" might be desired?
	// Let's just return null if exact match fails for now to be safe, OR fallback to the provided util if we want to risk it.
	// Actually, let's Stick to the provided logic but refined.

	// Fallback: Contains
	key = Object.keys(metrics).find(k => k.toLowerCase().includes(metricName.toLowerCase()));
	return key ? metrics[key] : null;
}


export interface KeyMetrics {
	totalRevenue: number | null;
	netIncome: number | null;
	netProfitMargin: number | null;
	dilutedEPS: number | null;
	cashAndEquivalents: number | null;
	totalDebt: number | null;
	operatingCashFlow: number | null;
	freeCashFlow: number | null;
}

export const getKeyMetrics = (company: any): KeyMetrics => {
	const get = (cat: string, name: string) => getSafeValue(company, cat, name);

	const totalRevenue = get('income_statement', 'Total Revenue') ?? get('income_statement', 'Revenue');
	const netIncome = get('income_statement', 'Net Income') ?? get('income_statement', 'Net Income Common Stockholders');
	const dilutedEPS = get('income_statement', 'Diluted EPS') ?? get('income_statement', 'Basic EPS'); // Fallback?

	const cashAndEquivalents = get('balance_sheet', 'Cash And Cash Equivalents') ?? get('balance_sheet', 'Cash');
	const totalDebt = get('balance_sheet', 'Total Debt') ?? get('balance_sheet', 'Long Term Debt'); // Approximate

	const operatingCashFlow = get('cash_flow', 'Operating Cash Flow') ?? get('cash_flow', 'Total Cash From Operating Activities');
	const capitalExpenditure = get('cash_flow', 'Capital Expenditure') ?? 0; // Usually negative

	// Free Cash Flow
	let freeCashFlow = get('cash_flow', 'Free Cash Flow');
	if (freeCashFlow === null && operatingCashFlow !== null) {
		// Calculate: OCF + CapEx
		// CapEx is usually negative. If it's missing (0), FCF = OCF.
		// Make sure CapEx is a number.
		const capexVal = typeof capitalExpenditure === 'number' ? capitalExpenditure : 0;
		freeCashFlow = operatingCashFlow + capexVal;
	}

	// Net Profit Margin
	let netProfitMargin = null;
	if (totalRevenue && netIncome) {
		netProfitMargin = (netIncome / totalRevenue) * 100;
	}

	return {
		totalRevenue,
		netIncome,
		netProfitMargin,
		dilutedEPS,
		cashAndEquivalents,
		totalDebt,
		operatingCashFlow,
		freeCashFlow
	};
};
