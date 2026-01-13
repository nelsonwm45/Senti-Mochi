/**
 * Bursa Malaysia News API Proxy
 * Fetches announcements from Bursa Malaysia API (client-side to bypass CORS)
 * Returns raw data - frontend will process and store in backend
 */

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const bursa_code = searchParams.get('company');
  
  if (!bursa_code) {
    return Response.json(
      { error: 'Company code is required' },
      { status: 400 }
    );
  }

  try {
    const url = `https://www.bursamalaysia.com/api/v1/announcements/search?ann_type=company&company=${bursa_code}&per_page=5&page=0`;
    
    const response = await fetch(url, {
      headers: {
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
      },
      next: { revalidate: 0 } // No caching
    });

    if (!response.ok) {
      console.error(`Bursa API error: ${response.status}`);
      return Response.json(
        { error: `Bursa API returned ${response.status}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return Response.json(data);
  } catch (error) {
    console.error('Error fetching from Bursa API:', error);
    return Response.json(
      { error: error instanceof Error ? error.message : 'Failed to fetch Bursa articles' },
      { status: 500 }
    );
  }
}
