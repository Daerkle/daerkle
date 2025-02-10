import { PivotLevels, Setup, SetupAnalysis, SetupType } from '../types/setups';

const TOLERANCE = 0.005; // 0.5% tolerance for pivot levels
const MIN_SUCCESS_PROBABILITY = 0.6;
const MIN_RR_RATIO = 1.5;

export function calculatePivotLevels(high: number, low: number, close: number): PivotLevels {
  const PP = (high + low + close) / 3;
  const R1 = (2 * PP) - low;
  const R2 = PP + (high - low);
  const S1 = (2 * PP) - high;
  const S2 = PP - (high - low);

  return { PP, R1, R2, S1, S2 };
}

function isNearPivotLevel(price: number, pivotLevel: number): boolean {
  const upperBound = pivotLevel * (1 + TOLERANCE);
  const lowerBound = pivotLevel * (1 - TOLERANCE);
  return price >= lowerBound && price <= upperBound;
}

function calculateRR(entry: number, target: number, stopLoss: number, type: SetupType): number {
  if (type === 'LONG') {
    return (target - entry) / (entry - stopLoss);
  }
  return (entry - target) / (stopLoss - entry);
}

function getRecommendation(probability: number, rr: number): Setup['recommendation'] {
  if (probability >= MIN_SUCCESS_PROBABILITY && rr >= MIN_RR_RATIO) {
    return 'ENTER';
  }
  if (probability <= 0.4 || rr < 1) {
    return 'AVOID';
  }
  return 'CAUTION';
}

export async function analyzeSetups(
  symbol: string,
  currentPrice: number,
  high: number,
  low: number,
  close: number
): Promise<SetupAnalysis> {
  const pivotLevels = calculatePivotLevels(high, low, close);
  const setups: Setup[] = [];

  // Check for long setups at support levels
  if (isNearPivotLevel(currentPrice, pivotLevels.S1)) {
    const stopLoss = pivotLevels.S2;
    const target = pivotLevels.PP;
    const rr = calculateRR(currentPrice, target, stopLoss, 'LONG');
    const probability = 0.65; // This should be calculated from historical data

    setups.push({
      type: 'LONG',
      entryPrice: currentPrice,
      stopLoss,
      target,
      probability,
      riskRewardRatio: rr,
      recommendation: getRecommendation(probability, rr),
      pivotLevel: 'S1',
      description: 'Long Setup: Rebound von S1 Support'
    });
  }

  // Check for short setups at resistance levels
  if (isNearPivotLevel(currentPrice, pivotLevels.R1)) {
    const stopLoss = pivotLevels.R2;
    const target = pivotLevels.PP;
    const rr = calculateRR(currentPrice, target, stopLoss, 'SHORT');
    const probability = 0.62; // This should be calculated from historical data

    setups.push({
      type: 'SHORT',
      entryPrice: currentPrice,
      stopLoss,
      target,
      probability,
      riskRewardRatio: rr,
      recommendation: getRecommendation(probability, rr),
      pivotLevel: 'R1',
      description: 'Short Setup: Rejection an R1 Resistance'
    });
  }

  return {
    symbol,
    currentPrice,
    pivotLevels,
    setups,
    timestamp: new Date().toISOString()
  };
}
