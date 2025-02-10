export interface PivotLevels {
  R5: number;
  R4: number;
  R3: number;
  R2: number;
  R1: number;
  P: number;
  S1: number;
  S2: number;
  S3: number;
  S4: number;
  S5: number;
}

export interface SetupAnalysis {
  type: 'long' | 'short';
  subType: 'pivot_bounce' | 'breakout' | 'support_confirmation';
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
  additionalTargets?: (number | null)[];
  trendDirection: 'up' | 'down' | 'sideways';
  confirmations: Record<string, boolean>;
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

export interface StockData {
  symbol: string;
  price: number;
  change: number;
  volume: number;
  volumeBuzz: number;
  pivots: PivotLevels;
  setups: SetupAnalysis[];
}
