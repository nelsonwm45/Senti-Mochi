
/**
 * Format a number as currency (USD)
 * @param value - Number to format
 * @returns Formatted currency string (e.g. "$1,234.56")
 */
export function formatCurrency(value: number): string {
	return new Intl.NumberFormat('en-US', {
		style: 'currency',
		currency: 'USD',
		minimumFractionDigits: 2,
		maximumFractionDigits: 2,
	}).format(value);
}

/**
 * Format a large number (Market Cap) with suffix (B, M, T)
 * @param value - Number to format
 * @returns Formatted string (e.g. "2.45B")
 */
export function formatMarketCap(value: number): string {
	if (value >= 1.0e12) {
		return (value / 1.0e12).toFixed(2) + 'T';
	} else if (value >= 1.0e9) {
		return (value / 1.0e9).toFixed(2) + 'B';
	} else if (value >= 1.0e6) {
		return (value / 1.0e6).toFixed(2) + 'M';
	} else {
		return value.toString();
	}
}

/**
 * Format a number with commas
 * @param value - Number to format
 * @returns Formatted string (e.g. "1,234,567")
 */
export function formatNumber(value: number): string {
	return new Intl.NumberFormat('en-US').format(value);
}
