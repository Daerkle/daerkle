import { NextResponse } from 'next/server';
import axios from 'axios';
import { SetupAnalysis } from '@/types/setup';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const symbol = searchParams.get('symbol');

  if (!symbol) {
    return NextResponse.json({ error: 'Symbol is required' }, { status: 400 });
  }

  console.log('[API] GET /api/pivot-analysis', { symbol });
  console.log('[API] Fetching from Python backend...');

  try {
    const response = await axios.get(`http://127.0.0.1:8000/api/pivot-analysis?symbol=${symbol}`);
    const setups: SetupAnalysis[] = response.data.setups;

    return NextResponse.json({
      symbol,
      setups
    });
  } catch (error) {
    console.log('[API] Error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch pivot analysis' },
      { status: 500 }
    );
  }
}
