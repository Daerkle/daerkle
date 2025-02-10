'use client';

import { useEffect, useRef } from 'react';
import { useSymbol } from '@/contexts/SymbolContext';
import LoadingSpinner from './LoadingSpinner';

declare global {
  interface Window {
    TradingView: any;
  }
}

interface ChartProps {
  className?: string;
}

export default function Chart({ className = '' }: ChartProps) {
  const { selectedSymbol } = useSymbol();
  const containerRef = useRef<HTMLDivElement>(null);
  const widgetRef = useRef<any>(null);

  useEffect(() => {
    const initializeChart = () => {
      if (!selectedSymbol || !containerRef.current) return;

      // Entferne vorhandenes Widget
      if (widgetRef.current) {
        containerRef.current.innerHTML = '';
      }

      const config = {
        width: '100%',
        height: '100%',
        symbol: selectedSymbol,
        interval: 'D',
        timezone: 'Europe/Berlin',
        theme: 'dark',
        style: '1',
        locale: 'de_DE',
        enable_publishing: false,
        hide_side_toolbar: true,
        allow_symbol_change: true,
        container_id: containerRef.current.id,
        studies: [
          { id: 'MASimple@tv-basicstudies', inputs: { length: 20 } },
          { id: 'MASimple@tv-basicstudies', inputs: { length: 50 } },
          { id: 'MASimple@tv-basicstudies', inputs: { length: 200 } }
        ]
      };

      // Erstelle neues Widget
      widgetRef.current = new window.TradingView.widget(config);
    };

    // Lade TradingView Script wenn nötig
    if (!window.TradingView) {
      const script = document.createElement('script');
      script.src = 'https://s3.tradingview.com/tv.js';
      script.async = true;
      script.onload = initializeChart;
      document.body.appendChild(script);
    } else {
      initializeChart();
    }

    // Cleanup
    return () => {
      if (widgetRef.current) {
        try {
          widgetRef.current.remove();
        } catch (e) {
          console.error('Error removing TradingView widget:', e);
        }
      }
    };
  }, [selectedSymbol]);

  if (!selectedSymbol) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        Wählen Sie ein Symbol aus der Watchlist
      </div>
    );
  }

  return (
    <div className={`h-full ${className}`}>
      <div
        id={`tradingview_${selectedSymbol}`}
        ref={containerRef}
        className="h-full"
      />
    </div>
  );
}
