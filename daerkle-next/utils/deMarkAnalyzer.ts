interface Candle {
  open: number;
  high: number;
  low: number;
  close: number;
  date?: Date;
}

interface Setup {
  active: boolean;
  countdown?: number;
  completed: boolean;
  direction: 'long' | 'short';
}

export class DeMarkAnalyzer {
  static analyzeTD9(candles: Candle[]): Setup {
    if (candles.length < 9) {
      return { active: false, completed: false, direction: 'long' };
    }

    // Get last 9 candles for analysis
    const lastNine = candles.slice(-9);
    
    // Check for TD Setup Long (9 consecutive closes less than the close 4 bars earlier)
    let setupLong = true;
    for (let i = 0; i < 9; i++) {
      if (lastNine[i].close >= candles[i + candles.length - 13].close) {
        setupLong = false;
        break;
      }
    }

    // Check for TD Setup Short (9 consecutive closes greater than the close 4 bars earlier)
    let setupShort = true;
    for (let i = 0; i < 9; i++) {
      if (lastNine[i].close <= candles[i + candles.length - 13].close) {
        setupShort = false;
        break;
      }
    }

    // Determine countdown
    let countdown = 0;
    if (setupLong || setupShort) {
      countdown = 9;
      // Additional countdown logic could be added here
    }

    return {
      active: setupLong || setupShort,
      countdown,
      completed: countdown === 13,
      direction: setupLong ? 'long' : 'short'
    };
  }

  static calculateDeMarkLevels(candles: Candle[]): { 
    levels: { [key: string]: number },
    setups: { long: Setup, short: Setup }
  } {
    const lastCandle = candles[candles.length - 1];
    
    // Calculate DeMark pivot points
    const high = lastCandle.high;
    const low = lastCandle.low;
    const close = lastCandle.close;
    
    let x = 0;
    if (close < lastCandle.open) { // Down close
      x = high + (2 * (low - close));
    } else { // Up close
      x = (2 * high) - low - close;
    }

    const levels = {
      R1: x / 2,
      PP: (high + low + close) / 3,
      S1: x / 2
    };

    // Analyze setups
    const setups = {
      long: this.analyzeTD9(candles),
      short: { ...this.analyzeTD9(candles), direction: 'short' as const }
    };

    return { levels, setups };
  }
}
