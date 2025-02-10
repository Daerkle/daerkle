'use client';

import { useEffect, useRef } from 'react';
import { createChart, ColorType } from 'lightweight-charts';
import useSWR from 'swr';

interface StockChartProps {
  symbol: string;
  timeframe: string;
}

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export default function StockChart({ symbol, timeframe }: StockChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const { data, error, isLoading } = useSWR(
    `/api/stock-data?symbol=${symbol}&timeframe=${timeframe}`,
    fetcher
  );

  useEffect(() => {
    if (!chartContainerRef.current || !data) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#ffffff' },
        textColor: '#333',
      },
      width: chartContainerRef.current.clientWidth,
      height: 400,
    });

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    candlestickSeries.setData(data.map((item: any) => ({
      time: item.time,
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close,
    })));

    chart.timeScale().fitContent();

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [data]);

  if (error) return <div>Failed to load chart data</div>;
  if (isLoading) return <div>Loading...</div>;

  return <div ref={chartContainerRef} />;
}
