import { NextResponse } from 'next/server';
import axios from 'axios';
import { API_CONFIG, debug } from '@/config/api';

export async function GET() {
  debug('GET /api/watchlist');
  try {
    const response = await axios.get(`${API_CONFIG.BASE_URL}/api/watchlist`);
    debug('Response:', response.data);
    return NextResponse.json(response.data);
  } catch (error) {
    debug('Error:', error);
    console.error('Error reading watchlist:', error);
    return NextResponse.json(
      { error: 'Failed to read watchlist' },
      { status: 500 }
    );
  }
}

export async function POST(request: Request) {
  try {
    const { symbol } = await request.json();
    debug('POST /api/watchlist', { symbol });
    
    if (!symbol) {
      return NextResponse.json(
        { error: 'Symbol is required' },
        { status: 400 }
      );
    }

    const response = await axios.post(`${API_CONFIG.BASE_URL}/api/watchlist`, { symbol });
    debug('Response:', response.data);
    return NextResponse.json(response.data);
  } catch (error: any) {
    debug('Error:', error.response?.data || error);
    console.error('Error adding to watchlist:', error);
    
    // FastAPI Fehler weiterleiten
    if (error.response?.data?.detail) {
      return NextResponse.json(
        { error: error.response.data.detail },
        { status: error.response.status }
      );
    }
    
    return NextResponse.json(
      { error: 'Failed to add to watchlist' },
      { status: 500 }
    );
  }
}

export async function DELETE(request: Request) {
  try {
    const { symbol } = await request.json();
    debug('DELETE /api/watchlist', { symbol });
    
    if (!symbol) {
      return NextResponse.json(
        { error: 'Symbol is required' },
        { status: 400 }
      );
    }

    const response = await axios.delete(`${API_CONFIG.BASE_URL}/api/watchlist`, {
      data: { symbol }
    });
    debug('Response:', response.data);
    return NextResponse.json(response.data);
  } catch (error: any) {
    debug('Error:', error.response?.data || error);
    console.error('Error removing from watchlist:', error);
    
    // FastAPI Fehler weiterleiten
    if (error.response?.data?.detail) {
      return NextResponse.json(
        { error: error.response.data.detail },
        { status: error.response.status }
      );
    }
    
    return NextResponse.json(
      { error: 'Failed to remove from watchlist' },
      { status: 500 }
    );
  }
}
