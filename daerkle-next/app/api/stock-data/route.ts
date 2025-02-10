import { NextResponse } from 'next/server';
import { PivotLevels, SetupAnalysis } from '@/types/setup';

interface HistoricalData {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// Basis-Funktionen
async function fetchStockData(symbol: string) {
  try {
    const response = await fetch(`http://localhost:8000/api/stock-data?symbol=${symbol}&timeframe=1d`);
    if (!response.ok) throw new Error('Failed to fetch stock data');
    const data = await response.json();
    
    return data;
  } catch (error) {
    console.error('Error fetching stock data:', error);
    return null;
  }
}

function calculatePivots(data: HistoricalData[]): PivotLevels {
  const high = data[data.length - 1].high;
  const low = data[data.length - 1].low;
  const close = data[data.length - 1].close;

  const pp = (high + low + close) / 3;
  const r1 = (2 * pp) - low;
  const r2 = pp + (high - low);
  const r3 = high + 2 * (pp - low);
  const s1 = (2 * pp) - high;
  const s2 = pp - (high - low);
  const s3 = low - 2 * (high - pp);

  return { pp, r1, r2, r3, s1, s2, s3 };
}

function calculateBestTime(data: HistoricalData[], type: 'long' | 'short'): string {
  const hourlyStats: { [key: string]: number } = {};
  
  for (let i = 1; i < data.length; i++) {
    const current = data[i];
    const previous = data[i - 1];
    const date = new Date(current.timestamp);
    const hour = date.getHours().toString().padStart(2, '0');
    const minute = Math.floor(date.getMinutes() / 15) * 15;
    const timeKey = `${hour}:${minute.toString().padStart(2, '0')}`;

    if (type === 'long' && current.close > previous.close) {
      hourlyStats[timeKey] = (hourlyStats[timeKey] || 0) + 1;
    } else if (type === 'short' && current.close < previous.close) {
      hourlyStats[timeKey] = (hourlyStats[timeKey] || 0) + 1;
    }
  }

  // Finde die erfolgreichste Zeit
  let bestTime = '09:30';
  let maxSuccess = 0;
  
  for (const [time, success] of Object.entries(hourlyStats)) {
    if (success > maxSuccess) {
      maxSuccess = success;
      bestTime = time;
    }
  }

  return bestTime;
}

// Analyse-Hilfsfunktionen bleiben gleich...
function checkVolumeIncrease(data: HistoricalData[]): boolean {
  const recentVolumes = data.slice(-5).map(d => d.volume);
  return recentVolumes[recentVolumes.length - 1] > recentVolumes[recentVolumes.length - 2];
}

function checkReversalCandle(data: HistoricalData[]): boolean {
  const lastCandle = data[data.length - 1];
  const bodySize = Math.abs(lastCandle.close - lastCandle.open);
  const upperWick = lastCandle.high - Math.max(lastCandle.open, lastCandle.close);
  const lowerWick = Math.min(lastCandle.open, lastCandle.close) - lastCandle.low;
  
  return (lowerWick > bodySize * 2) || (upperWick > bodySize * 2);
}

function detectCluster(pivots: PivotLevels[], price: number, tolerance: number): boolean {
  const allLevels = [
    pivots[0].pp, 
    pivots[0].r1, 
    pivots[0].r2, 
    pivots[0].s1, 
    pivots[0].s2
  ];
  const nearbyLevels = allLevels.filter(level => Math.abs(price - level) <= tolerance);
  return nearbyLevels.length >= 2;
}

function countTests(data: HistoricalData[], level: number, tolerance: number): number {
  let tests = 0;
  for (let i = data.length - 10; i < data.length; i++) {
    if (Math.abs(data[i].high - level) <= tolerance || Math.abs(data[i].low - level) <= tolerance) {
      tests++;
    }
  }
  return tests;
}

function determineTrend(data: HistoricalData[], pp: number): 'up' | 'down' | 'sideways' {
  const lastClose = data[data.length - 1].close;
  const sma20 = data.slice(-20).reduce((sum, bar) => sum + bar.close, 0) / 20;
  
  if (lastClose > sma20 && lastClose > pp) return 'up';
  if (lastClose < sma20 && lastClose < pp) return 'down';
  return 'sideways';
}

function calculateVolumeBuzz(data: HistoricalData[]): number {
  const last20Days = data.slice(-21, -1);
  const avgVolume = last20Days.reduce((sum, day) => sum + day.volume, 0) / 20;
  const currentVolume = data[data.length - 1].volume;
  return ((currentVolume / avgVolume) * 100) - 100;
}

// Setup-Erkennungsfunktionen
function findLongSetups(
  data: HistoricalData[],
  pivots: PivotLevels,
  timeframe: string
): SetupAnalysis[] {
  const setups: SetupAnalysis[] = [];
  const price = data[data.length - 1].close;
  const tolerance = price * 0.005;

  // Support-Levels testen
  const supportLevels = [
    { level: pivots.s1, name: 'S1' },
    { level: pivots.s2, name: 'S2' },
    { level: pivots.s3, name: 'S3' }
  ];

  for (const { level, name } of supportLevels) {
    if (Math.abs(data[data.length - 1].low - level) <= tolerance) {
      const hasVolume = checkVolumeIncrease(data);
      const hasReversal = checkReversalCandle(data);
      const cluster = detectCluster([pivots], price, tolerance);
      const tests = countTests(data, level, tolerance);
      const trend = determineTrend(data, pivots.pp);
      const volumeBuzz = calculateVolumeBuzz(data);

      if (hasVolume && hasReversal) {
        const setup: SetupAnalysis = {
          type: 'long',
          subType: 'pivot_bounce',
          timeframe,
          entry: price,
          stopLoss: Math.min(level * 0.99, data[data.length - 1].low * 0.99),
          target: pivots.pp,
          probability: tests >= 2 ? 65 : 55,
          rr: (pivots.pp - price) / (price - (level * 0.99)),
          volumeBuzz,
          quality: cluster && tests >= 2 ? 'A+' : hasVolume ? 'A' : 'B',
          pivotLevel: name,
          reason: `Bounce from ${name}`,
          bestTime: calculateBestTime(data, 'long'),
          cluster,
          divergence: false,
          repeatedTests: tests,
          additionalTargets: [pivots.r1],
          trendDirection: trend,
          confirmations: {
            volume: hasVolume,
            reversal: hasReversal,
            trend: trend === 'up',
            cluster,
            multipleTests: tests >= 2
          }
        };

        setups.push(setup);
      }
    }
  }

  return setups;
}

function findShortSetups(
  data: HistoricalData[],
  pivots: PivotLevels,
  timeframe: string
): SetupAnalysis[] {
  const setups: SetupAnalysis[] = [];
  const price = data[data.length - 1].close;
  const tolerance = price * 0.005;

  // Resistance-Levels testen
  const resistanceLevels = [
    { level: pivots.r1, name: 'R1' },
    { level: pivots.r2, name: 'R2' },
    { level: pivots.r3, name: 'R3' }
  ];

  for (const { level, name } of resistanceLevels) {
    if (Math.abs(data[data.length - 1].high - level) <= tolerance) {
      const hasVolume = checkVolumeIncrease(data);
      const hasReversal = checkReversalCandle(data);
      const cluster = detectCluster([pivots], price, tolerance);
      const tests = countTests(data, level, tolerance);
      const trend = determineTrend(data, pivots.pp);
      const volumeBuzz = calculateVolumeBuzz(data);

      if (hasVolume && hasReversal) {
        const setup: SetupAnalysis = {
          type: 'short',
          subType: 'resistance_rejection',
          timeframe,
          entry: price,
          stopLoss: Math.max(level * 1.01, data[data.length - 1].high * 1.01),
          target: pivots.pp,
          probability: tests >= 2 ? 65 : 55,
          rr: (price - pivots.pp) / ((level * 1.01) - price),
          volumeBuzz,
          quality: cluster && tests >= 2 ? 'A+' : hasVolume ? 'A' : 'B',
          pivotLevel: name,
          reason: `Rejection at ${name}`,
          bestTime: calculateBestTime(data, 'short'),
          cluster,
          divergence: false,
          repeatedTests: tests,
          additionalTargets: [pivots.s1],
          trendDirection: trend,
          confirmations: {
            volume: hasVolume,
            reversal: hasReversal,
            trend: trend === 'down',
            cluster,
            multipleTests: tests >= 2
          }
        };

        setups.push(setup);
      }
    }
  }

  return setups;
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const symbol = searchParams.get('symbol');
  const timeframe = searchParams.get('timeframe') || '1d';

  if (!symbol) {
    return new Response('Symbol parameter is required', { status: 400 });
  }

  try {
    const data = await fetchStockData(symbol);
    if (!data) {
      return new Response('Failed to fetch stock data', { status: 500 });
    }

    const lastBar = data[data.length - 1];
    const pivots = calculatePivots(data);
    const volumeBuzz = calculateVolumeBuzz(data);
    const trend = determineTrend(data, pivots.pp);
    const longSetups = findLongSetups(data, pivots, timeframe);
    const shortSetups = findShortSetups(data, pivots, timeframe);

    return NextResponse.json({
      symbol,
      price: lastBar.close,
      change: ((lastBar.close - data[data.length - 2].close) / data[data.length - 2].close) * 100,
      volume: lastBar.volume,
      volumeBuzz,
      pivots,
      trend,
      setups: [...longSetups, ...shortSetups],
      hasReversal: checkReversalCandle(data),
      volumeIncreasing: checkVolumeIncrease(data)
    });
  } catch (error) {
    console.error('Error in stock-data route:', error);
    return new Response('Internal server error', { status: 500 });
  }
}
