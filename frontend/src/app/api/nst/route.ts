import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
    const { searchParams } = new URL(request.url);
    const keywords = searchParams.get('keywords') || '';
    const category = searchParams.get('category') || '';
    const sort = searchParams.get('sort') || 'DESC';
    const pageSize = searchParams.get('page_size') || '20';
    const page = searchParams.get('page') || '0';

    if (!keywords) {
        return NextResponse.json(
            { error: 'Missing keywords parameter' },
            { status: 400 }
        );
    }

    try {
        const url = `https://www.nst.com.my/api/search?keywords=${encodeURIComponent(keywords)}&category=${category}&sort=${sort}&page_size=${pageSize}&page=${page}`;

        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            },
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('Error fetching NST articles:', error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to fetch articles' },
            { status: 500 }
        );
    }
}
