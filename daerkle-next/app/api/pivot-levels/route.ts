import { NextResponse } from 'next/server';
import axios from 'axios';

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const symbol = searchParams.get('symbol');

  if (!symbol) {
    return NextResponse.json({ error: 'Symbol is required' }, { status: 400 });
  }

  try {
    const response = await axios.get(`${API_BASE_URL}/api/pivot-analysis`, {
      params: { symbol }
    });

    return NextResponse.json(response.data);
  } catch (error) {
    console.error('Error fetching pivot analysis:', error);
    return NextResponse.json(
      { error: 'Failed to fetch pivot analysis' },
      { status: 500 }
    );
  }
}
