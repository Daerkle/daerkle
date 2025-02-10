'use client';

import { useParams } from 'next/navigation';
import { useState } from 'react';
import TradingViewChart from '@/components/TradingViewChart';
import PivotLevels from '@/components/PivotLevels';
import TimeframeSelector from '@/components/TimeframeSelector';

const intervalMap = {
  '1d': 'D',
  '1wk': 'W',
  '1mo': 'M'
};

export default function ChartPage() {
  const params = useParams();
  const symbol = typeof params.symbol === 'string' ? params.symbol : '';
  const [timeframe, setTimeframe] = useState('1d');

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">{symbol}</h1>
        <TimeframeSelector 
          value={timeframe} 
          onChange={setTimeframe} 
        />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-3">
          <TradingViewChart 
            symbol={symbol} 
            interval={intervalMap[timeframe as keyof typeof intervalMap]} 
          />
        </div>
        <div>
          <PivotLevels 
            symbol={symbol} 
            interval={timeframe}
          />
        </div>
      </div>
    </div>
  );
}
