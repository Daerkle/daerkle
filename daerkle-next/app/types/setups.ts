export type SetupType = 'LONG' | 'SHORT';

export interface PivotLevels {
  PP: number;
  R1: number;
  R2: number;
  S1: number;
  S2: number;
}

export interface Setup {
  type: SetupType;
  entryPrice: number;
  stopLoss: number;
  target: number;
  probability: number;
  riskRewardRatio: number;
  recommendation: 'ENTER' | 'AVOID' | 'CAUTION';
  pivotLevel: keyof PivotLevels;
  description: string;
}

export interface SetupAnalysis {
  symbol: string;
  currentPrice: number;
  pivotLevels: PivotLevels;
  setups: Setup[];
  timestamp: string;
}
