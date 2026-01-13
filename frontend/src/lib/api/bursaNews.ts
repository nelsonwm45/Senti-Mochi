import apiClient from '../apiClient';

export interface BursaNewsArticle {
  company_id: string;
  source: 'bursa';
  native_id: string;
  title: string;
  url: string;
  published_at: string; // ISO datetime
  content?: string;
}

/**
 * Fetch Bursa news from the client-side API and store in backend
 * This is necessary because Bursa Malaysia API has CORS restrictions
 */
export async function fetchAndStoreBursaNews(
  companies: Array<{ id: string; ticker: string; name: string }>
): Promise<{ saved: number; total: number }> {
  try {
    const articlesToStore: BursaNewsArticle[] = [];

    for (const company of companies) {
      const bursa_code = company.ticker.split('.')[0];
      
      try {
        // Fetch from our frontend API proxy
        const response = await fetch(`/api/bursa?company=${bursa_code}`);
        
        if (!response.ok) {
          console.warn(`Failed to fetch Bursa news for ${company.name}:`, response.status);
          continue;
        }

        const data = await response.json();
        
        if (!data.data || !Array.isArray(data.data)) {
          console.warn(`No data returned for ${company.name}`);
          continue;
        }

        // Parse the Bursa API response
        for (const item of data.data) {
          try {
            // Item format: [id, date_html, company_html, title_html]
            const dateMatch = item[1].match(/>([^<]+)<\/a>/);
            const dateStr = dateMatch ? dateMatch[1].trim() : '';

            const titleMatch = item[3].match(/href='([^']+)'[^>]*>(.*?)<\/a>/);
            const linkSuffix = titleMatch ? titleMatch[1] : '';
            const title = titleMatch ? titleMatch[2].trim() : 'Unknown Title';
            const link = linkSuffix ? `https://www.bursamalaysia.com${linkSuffix}` : '';

            const idMatch = link.match(/ann_id=(\d+)/);
            const native_id = idMatch 
              ? `bursa-${bursa_code}-${idMatch[1]}`
              : `bursa-${bursa_code}-${item[0]}`;

            // Parse date
            let published_at = new Date().toISOString();
            try {
              // Format: "13 Jan 2026, 05:44 pm"
              const parsedDate = new Date(dateStr);
              if (!isNaN(parsedDate.getTime())) {
                published_at = parsedDate.toISOString();
              }
            } catch (e) {
              console.warn(`Failed to parse date: ${dateStr}`);
            }

            articlesToStore.push({
              company_id: company.id,
              source: 'bursa',
              native_id,
              title,
              url: link,
              published_at,
              content: title
            });
          } catch (itemError) {
            console.warn(`Failed to parse article item:`, itemError);
          }
        }
      } catch (companyError) {
        console.warn(`Error fetching Bursa news for ${company.name}:`, companyError);
      }
    }

    // Send all articles to backend for storage
    if (articlesToStore.length > 0) {
      const storeResponse = await apiClient.post('/api/v1/news/store-articles', articlesToStore);
      return storeResponse.data;
    }

    return { saved: 0, total: 0 };
  } catch (error) {
    console.error('Error in fetchAndStoreBursaNews:', error);
    throw error;
  }
}
