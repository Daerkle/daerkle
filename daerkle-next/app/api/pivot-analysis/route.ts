import { NextResponse } from 'next/server';
import axios from 'axios';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const symbol = searchParams.get('symbol');

  if (!symbol) {
    return NextResponse.json({ error: 'Symbol is required' }, { status: 400 });
  }

  console.log('[API] GET /api/pivot-analysis', { symbol });

  try {
    // Hole die Daten von der stock-data Route
    const response = await axios.get(`http://localhost:3000/api/stock-data?symbol=${symbol}`);
    const data = response.data;

    // Extrahiere nur die Setup-Daten
    return NextResponse.json({
      symbol,
      setups: data.setups
    });
  } catch (error) {
    console.log('[API] Error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch pivot analysis' },
      { status: 500 }
    );
  }
}
