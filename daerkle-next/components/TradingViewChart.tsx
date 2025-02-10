'use client';

import { useEffect, useRef } from 'react';

interface TradingViewChartProps {
  symbol: string;
  interval?: string;
  theme?: 'light' | 'dark';
}

export default function TradingViewChart({ 
  symbol, 
  interval = 'D',
  theme = 'light'
}: TradingViewChartProps) {
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/tv.js';
    script.async = true;
    script.onload = () => {
      if (typeof TradingView !== 'undefined' && container.current) {
        new TradingView.widget({
          container_id: container.current.id,
          symbol: symbol,
          interval: interval,
          timezone: 'Europe/Berlin',
          theme: theme,
          style: '1',
          locale: 'de',
          toolbar_bg: '#f1f3f6',
          enable_publishing: false,
          hide_side_toolbar: false,
          allow_symbol_change: true,
          save_image: false,
          height: 500,
          width: '100%',
        });
      }
    };
    document.head.appendChild(script);

    return () => {
      document.head.removeChild(script);
    };
  }, [symbol, interval, theme]);

  return (
    <div 
      id={`tradingview_${symbol.toLowerCase()}`} 
      ref={container}
      style={{ width: '100%', height: '500px' }}
    />
  );
}
