'use client';

import { useEffect, useState } from 'react';
import LoadingSpinner from './LoadingSpinner';
import toast from 'react-hot-toast';

interface PivotLevels {
  standard: {
    levels: {
      [key: string]: number;
    };
    history: {
      [key: string]: [boolean, string, string];
    };
    status: {
      status: string;
      color: string;
      distance: string;
    };
  };
  demark: {
    levels: {
      [key: string]: number;
    };
    history: {
      [key: string]: [boolean, string, string];
    };
  };
}

interface Setup {
  active: boolean;
  trigger: number;
  target: number;
  distance: string;
}

interface Setups {
  long: Setup;
  short: Setup;
}

interface ApiResponse {
  pivots: {
    [timeframe: string]: PivotLevels;
  };
  setups: {
    [timeframe: string]: Setups;
  };
}

interface PivotLevelsProps {
  symbol: string;
}

const TIMEFRAMES = {
  "1d": "Tag",
  "1w": "Woche",
  "1m": "Monat"
};

const DEBUG = true;
const debug = (...args: any[]) => {
  if (DEBUG) {
    console.log('[PivotLevels]', ...args);
  }
};

export default function PivotLevels({ symbol }: PivotLevelsProps) {
  const [data, setData] = useState<ApiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTimeframe, setActiveTimeframe] = useState<string>("1d");

  useEffect(() => {
    debug('Component mounted/updated with symbol:', symbol);
    const fetchAnalysis = async () => {
      if (!symbol) {
        debug('No symbol provided');
        return;
      }
      
      try {
        debug('Fetching analysis for symbol:', symbol);
        setLoading(true);
        const response = await fetch(`/api/pivot-analysis?symbol=${symbol}`);
        debug('Response status:', response.status);
        
        if (!response.ok) {
          throw new Error('Failed to fetch pivot analysis');
        }
        
        const responseData = await response.json();
        debug('Received data:', responseData);
        
        if (!responseData.pivots) {
          debug('No pivot data in response');
          throw new Error('Invalid response format');
        }
        
        setData(responseData);
      } catch (err) {
        const error = err instanceof Error ? err.message : 'An error occurred';
        debug('Error:', error);
        toast.error(`Fehler beim Laden der Pivot-Analyse: ${error}`);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [symbol]);

  debug('Rendering with data:', { data, loading, activeTimeframe });

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <LoadingSpinner size="lg" className="mx-auto" />
      </div>
    );
  }

  if (!data || !data.pivots || !data.pivots[activeTimeframe]) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500">
        Keine Pivot-Daten verfügbar
      </div>
    );
  }

  const timeframeData = data.pivots[activeTimeframe];
  const setups = data.setups[activeTimeframe];

  return (
    <div className="h-full flex flex-col text-xs">
      {/* Timeframe Selector */}
      <div className="flex space-x-1 mb-2 sticky top-0 bg-white z-10 py-1">
        {Object.entries(TIMEFRAMES).map(([tf, label]) => (
          <button
            key={tf}
            onClick={() => setActiveTimeframe(tf)}
            className={`px-2 py-0.5 rounded ${
              activeTimeframe === tf
                ? 'bg-blue-100 text-blue-700 font-medium'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Setup Status - Inline */}
      <div className="flex gap-2 mb-2">
        {setups.long.active && (
          <div className="text-green-600">
            <span className="font-medium">Long</span>
            {' '}{setups.long.trigger.toFixed(2)} → {setups.long.target.toFixed(2)} ({setups.long.distance})
          </div>
        )}
        {setups.short.active && (
          <div className="text-red-600">
            <span className="font-medium">Short</span>
            {' '}{setups.short.trigger.toFixed(2)} → {setups.short.target.toFixed(2)} ({setups.short.distance})
          </div>
        )}
      </div>

      {/* Pivot Status - Inline */}
      <div className={`mb-2 px-2 py-1 rounded ${
        timeframeData.standard.status.color === '#10B981' ? 'bg-green-50 text-green-700' :
        timeframeData.standard.status.color === '#EF4444' ? 'bg-red-50 text-red-700' :
        'bg-gray-50 text-gray-700'
      }`}>
        <span className="font-medium">Status:</span>
        {' '}{timeframeData.standard.status.status} ({timeframeData.standard.status.distance})
      </div>

      {/* Pivot Levels - Kompakte Tabelle */}
      <div className="flex-1 overflow-auto">
        <table className="w-full">
          <thead className="sticky top-0 bg-white">
            <tr className="text-gray-500">
              <th className="text-left py-1 px-1">Level</th>
              <th className="text-right py-1 px-1">Std</th>
              <th className="text-right py-1 px-1">DeM</th>
              <th className="text-right py-1 px-1">Status</th>
            </tr>
          </thead>
          <tbody className="text-xs">
            {['R5', 'R4', 'R3', 'R2', 'R1', 'P', 'S1', 'S2', 'S3', 'S4', 'S5'].map((level, index) => {
              const standardValue = timeframeData.standard.levels[level];
              const demarkValue = timeframeData.demark.levels[level];
              const [reached, date, status] = timeframeData.standard.history[level] || [false, '', ''];
              const isCurrentLevel = timeframeData.standard.status.status.includes(level);

              return (
                <tr key={level} className={`
                  ${index % 2 === 0 ? 'bg-gray-50' : 'bg-white'}
                  ${isCurrentLevel ? '!bg-blue-50' : ''}
                  hover:bg-gray-100
                `}>
                  <td className="py-0.5 px-1">{level}</td>
                  <td className="text-right px-1">
                    {standardValue ? standardValue.toFixed(1) : '-'}
                  </td>
                  <td className="text-right px-1">
                    {demarkValue ? demarkValue.toFixed(1) : '-'}
                  </td>
                  <td className="text-right px-1">
                    {reached ? (
                      <span className="text-gray-500">{date}</span>
                    ) : (
                      <span className="text-blue-500">{status}</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
