export interface PivotLevels {
  pp: number;
  r1: number;
  r2: number;
  r3: number;
  s1: number;
  s2: number;
  s3: number;
}

export interface SetupAnalysis {
  type: 'long' | 'short';
  subType: 'pivot_bounce' | 'breakout' | 'support_confirmation' | 'resistance_rejection' | 'support_breakdown' | 'resistance_failure';
  timeframe: string;
  entry: number;
  target: number;
  stopLoss: number;
  trailingStop?: number;
  rr: number;
  probability: number;
  volumeBuzz: number;
  pivotLevel: string;
  quality: 'A+' | 'A' | 'B' | 'avoid';
  reason: string;
  bestTime: string;
  cluster: boolean;
  divergence: boolean;
  repeatedTests: number;
  additionalTargets: (number | null)[];
  trendDirection: 'up' | 'down' | 'sideways';
  confirmations: {
    volume?: boolean;
    reversal?: boolean;
    trend?: boolean;
    priceAction?: boolean;
    risingLows?: boolean;
    multipleTests?: boolean;
    fallingHighs?: boolean;
  };
}

export interface SetupFilters {
  quality: ('A+' | 'A' | 'B')[];
  type: ('long' | 'short')[];
  minRR: number;
  minProbability: number;
  minVolumeBuzz: number;
  timeframes: string[];
  setupTypes: string[];
}
