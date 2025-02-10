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

function calculateVolumeBuzz(data: HistoricalData[]): number {
  const last20Days = data.slice(-21, -1);
  const avgVolume = last20Days.reduce((sum, day) => sum + day.volume, 0) / 20;
  const currentVolume = data[data.length - 1].volume;
  return ((currentVolume / avgVolume) * 100) - 100;
}

function detectCluster(pivots: PivotLevels[], price: number, tolerance: number): boolean {
  const allLevels = pivots.flatMap(p => [p.pp, p.r1, p.r2, p.s1, p.s2]);
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

function detectDivergence(data: HistoricalData[]): boolean {
  // Vereinfachte RSI-Divergenz-Erkennung
  const rsiPeriod = 14;
  const lastRSI = calculateRSI(data.slice(-rsiPeriod));
  const prevRSI = calculateRSI(data.slice(-rsiPeriod * 2, -rsiPeriod));
  const priceChange = data[data.length - 1].close - data[data.length - rsiPeriod].close;
  
  return (lastRSI > prevRSI && priceChange < 0) || (lastRSI < prevRSI && priceChange > 0);
}

function calculateRSI(data: HistoricalData[]): number {
  let gains = 0, losses = 0;
  
  for (let i = 1; i < data.length; i++) {
    const change = data[i].close - data[i-1].close;
    if (change >= 0) gains += change;
    else losses -= change;
  }
  
  const avgGain = gains / data.length;
  const avgLoss = losses / data.length;
  const rs = avgGain / avgLoss;
  return 100 - (100 / (1 + rs));
}

function determineQuality(setup: Partial<SetupAnalysis>): 'A+' | 'A' | 'B' | 'avoid' {
  const { rr, probability, volumeBuzz, cluster, repeatedTests } = setup;
  
  if (rr! >= 1.5 && probability! >= 60 && volumeBuzz! >= 50 && cluster && repeatedTests! >= 3) {
    return 'A+';
  }
  if (rr! >= 1.3 && probability! >= 55 && volumeBuzz! >= 30 && (cluster || repeatedTests! >= 2)) {
    return 'A';
  }
  if (rr! >= 1.2 && probability! >= 50 && volumeBuzz! >= 20) {
    return 'B';
  }
  return 'avoid';
}

function analyzePivotSetups(
  data: HistoricalData[],
  pivots: PivotLevels[],
  timeframe: string
): SetupAnalysis[] {
  const setups: SetupAnalysis[] = [];
  const lastBar = data[data.length - 1];
  const price = lastBar.close;
  const tolerance = price * 0.005; // 0.5% Toleranz
  const volumeBuzz = calculateVolumeBuzz(data);
  const hasCluster = detectCluster(pivots, price, tolerance);

  // Trend-Bestimmung
  const trendDirection = determineTrend(data, pivots[0].pp);

  // 1. Pivot Point Bounce (Long)
  for (const pivot of pivots) {
    const supportLevels = [pivot.s1, pivot.s2, pivot.s3];
    
    for (const level of supportLevels) {
      if (Math.abs(price - level) <= tolerance) {
        const volumeIncreasing = checkVolumeIncrease(data);
        const hasReversal = checkReversalCandle(data);
        
        if (volumeIncreasing && hasReversal) {
          const stopLoss = Math.min(price * 0.99, level - (price * 0.005));
          const target = pivot.r1;
          const rr = Math.abs((target - price) / (price - stopLoss));
          const tests = countTests(data, level, tolerance);
          const hasDivergence = detectDivergence(data);
          
          const setup: SetupAnalysis = {
            type: 'long',
            subType: 'pivot_bounce',
            timeframe,
            entry: price,
            target,
            stopLoss,
            trailingStop: price + (price - stopLoss), // Trailing Stop bei 1R
            rr,
            probability: calculateProbability(data, 'long', level),
            volumeBuzz,
            pivotLevel: `S${supportLevels.indexOf(level) + 1}`,
            quality: 'avoid',
            reason: 'Pivot Point Bounce',
            bestTime: determineBestTime(data, 'long'),
            cluster: hasCluster,
            divergence: hasDivergence,
            repeatedTests: tests,
            additionalTargets: [pivot.r2, pivot.r3],
            trendDirection,
            confirmations: {
              volume: volumeIncreasing,
              reversal: hasReversal,
              trend: trendDirection === 'up'
            }
          };
          
          setup.quality = determineQuality(setup);
          if (setup.quality !== 'avoid') {
            setups.push(setup);
          }
        }
      }
    }
  }

  // 2. Resistance Breakout
  for (const pivot of pivots) {
    const resistanceLevels = [pivot.r1, pivot.r2];
    
    for (const level of resistanceLevels) {
      if (price > level && Math.abs(price - level) <= tolerance * 2) {
        const priceChange = (price - data[data.length - 2].close) / data[data.length - 2].close * 100;
        const volumeHigh = volumeBuzz >= 20;
        
        if (priceChange <= 2 && volumeHigh) {
          const stopLoss = level * 0.995; // Knapp unter dem durchbrochenen Level
          const target = level === pivot.r1 ? pivot.r2 : pivot.r3;
          const rr = Math.abs((target - price) / (price - stopLoss));
          
          const setup: SetupAnalysis = {
            type: 'long',
            subType: 'breakout',
            timeframe,
            entry: price,
            target,
            stopLoss,
            trailingStop: price + (price - stopLoss),
            rr,
            probability: calculateProbability(data, 'long', level),
            volumeBuzz,
            pivotLevel: level === pivot.r1 ? 'R1' : 'R2',
            quality: 'avoid',
            reason: 'Resistance Breakout',
            bestTime: determineBestTime(data, 'long'),
            cluster: hasCluster,
            divergence: false,
            repeatedTests: countTests(data, level, tolerance),
            additionalTargets: [level === pivot.r1 ? pivot.r3 : null].filter(Boolean),
            trendDirection,
            confirmations: {
              volume: volumeHigh,
              priceAction: priceChange <= 2,
              trend: trendDirection === 'up'
            }
          };
          
          setup.quality = determineQuality(setup);
          if (setup.quality !== 'avoid') {
            setups.push(setup);
          }
        }
      }
    }
  }

  // 3. Support Confirmation
  for (const pivot of pivots) {
    const supportLevels = [pivot.s1, pivot.s2];
    
    for (const level of supportLevels) {
      const tests = countTests(data, level, tolerance);
      if (tests >= 2 && checkRisingLows(data, level)) {
        const stopLoss = level * 0.99;
        const target = pivot.r1;
        const rr = Math.abs((target - price) / (price - stopLoss));
        
        const setup: SetupAnalysis = {
          type: 'long',
          subType: 'support_confirmation',
          timeframe,
          entry: price,
          target,
          stopLoss,
          trailingStop: price + (price - stopLoss),
          rr,
          probability: calculateProbability(data, 'long', level),
          volumeBuzz,
          pivotLevel: level === pivot.s1 ? 'S1' : 'S2',
          quality: 'avoid',
          reason: 'Support Confirmation',
          bestTime: determineBestTime(data, 'long'),
          cluster: hasCluster,
          divergence: detectDivergence(data),
          repeatedTests: tests,
          additionalTargets: [pivot.r2],
          trendDirection,
          confirmations: {
            risingLows: true,
            multipleTests: tests >= 2,
            trend: trendDirection === 'up'
          }
        };
        
        setup.quality = determineQuality(setup);
        if (setup.quality !== 'avoid') {
          setups.push(setup);
        }
      }
    }
  }

  // Short Setups analog zu den Long Setups implementieren...
  // (Resistance Rejection, Support Breakdown, Resistance Failure)

  return setups;
}

function checkVolumeIncrease(data: HistoricalData[]): boolean {
  const recentVolumes = data.slice(-5).map(d => d.volume);
  return recentVolumes[recentVolumes.length - 1] > recentVolumes[recentVolumes.length - 2];
}

function checkReversalCandle(data: HistoricalData[]): boolean {
  const lastCandle = data[data.length - 1];
  const bodySize = Math.abs(lastCandle.close - lastCandle.open);
  const upperWick = lastCandle.high - Math.max(lastCandle.open, lastCandle.close);
  const lowerWick = Math.min(lastCandle.open, lastCandle.close) - lastCandle.low;
  
  // Hammer oder Shooting Star
  return (lowerWick > bodySize * 2) || (upperWick > bodySize * 2);
}

function checkRisingLows(data: HistoricalData[], level: number): boolean {
  const relevantData = data.slice(-10);
  let lastLow = -Infinity;
  let risingLows = true;
  
  for (const bar of relevantData) {
    if (Math.abs(bar.low - level) <= level * 0.005) {
      if (bar.low <= lastLow) {
        risingLows = false;
        break;
      }
      lastLow = bar.low;
    }
  }
  
  return risingLows;
}

function determineTrend(data: HistoricalData[], pp: number): 'up' | 'down' | 'sideways' {
  const ma20 = calculateMA(data, 20);
  const lastClose = data[data.length - 1].close;
  
  if (lastClose > ma20 && lastClose > pp) return 'up';
  if (lastClose < ma20 && lastClose < pp) return 'down';
  return 'sideways';
}

function calculateMA(data: HistoricalData[], period: number): number {
  const prices = data.slice(-period).map(d => d.close);
  return prices.reduce((sum, price) => sum + price, 0) / period;
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const symbol = searchParams.get('symbol');
  const timeframe = searchParams.get('timeframe') || '1d';
  
  if (!symbol) {
    return NextResponse.json({ error: 'Symbol is required' }, { status: 400 });
  }

  try {
    const data = await fetchStockData(symbol);
    if (!data || data.length < 2) {
      return NextResponse.json({ error: 'Failed to fetch stock data' }, { status: 500 });
    }

    const currentBar = data[data.length - 1];
    const previousBar = data[data.length - 2];
    const volumeBuzz = calculateVolumeBuzz(data);
    
    // Calculate percentage change
    const change = ((currentBar.close - previousBar.close) / previousBar.close) * 100;
    
    return NextResponse.json({ 
      price: currentBar.close,
      change: change,
      volume: currentBar.volume,
      volumeBuzz: volumeBuzz,
      symbol: symbol,
      name: symbol // Using symbol as name since we don't have company names
    });
  } catch (error) {
    console.error('Error fetching stock data:', error);
    return NextResponse.json({ error: 'Failed to fetch stock data' }, { status: 500 });
  }
}
