import { NextResponse } from 'next/server';
import axios from 'axios';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const symbol = searchParams.get('symbol');

  if (!symbol) {
    return NextResponse.json({ error: 'Symbol is required' }, { status: 400 });
  }

  console.log('[API] GET /api/pivot-levels', { symbol });
  console.log('[API] Fetching from Python backend...');

  try {
    const response = await axios.get(`http://127.0.0.1:8000/api/pivot-analysis-old?symbol=${symbol}`);
    const data = response.data;

    return NextResponse.json(data);
  } catch (error) {
    console.log('[API] Error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch pivot levels' },
      { status: 500 }
    );
  }
}
