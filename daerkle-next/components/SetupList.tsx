import { useState, useEffect } from 'react';
import { SetupAnalysis, SetupFilters } from '@/types/setup';

interface SetupListProps {
  symbol: string;
}

export default function SetupList({ symbol }: SetupListProps) {
  const [setups, setSetups] = useState<SetupAnalysis[]>([]);
  const [filters, setFilters] = useState<SetupFilters>({
    quality: ['A+', 'A', 'B'],
    type: ['long', 'short'],
    minRR: 1.2,
    minProbability: 50,
    minVolumeBuzz: 20,
    timeframes: ['1d', '1w', '1m'],
    setupTypes: ['pivot_bounce', 'breakout', 'support_confirmation']
  });

  useEffect(() => {
    const fetchSetups = async () => {
      try {
        const response = await fetch(`/api/stock-data?symbol=${symbol}`);
        const data = await response.json();
        if (data.setups) {
          setSetups(data.setups);
        }
      } catch (error) {
        console.error('Error fetching setups:', error);
      }
    };

    fetchSetups();
  }, [symbol]);

  const filteredSetups = setups.filter(setup => {
    return filters.quality.includes(setup.quality) &&
           filters.type.includes(setup.type) &&
           setup.rr >= filters.minRR &&
           setup.probability >= filters.minProbability &&
           setup.volumeBuzz >= filters.minVolumeBuzz &&
           filters.timeframes.includes(setup.timeframe) &&
           filters.setupTypes.includes(setup.subType);
  });

  return (
    <div className="space-y-4">
      {/* Filter Controls */}
      <div className="flex flex-wrap gap-2 mb-4">
        <select 
          className="text-xs border rounded px-2 py-1"
          multiple
          value={filters.quality}
          onChange={(e) => setFilters(prev => ({
            ...prev,
            quality: Array.from(e.target.selectedOptions, option => option.value as 'A+' | 'A' | 'B')
          }))}
        >
          <option value="A+">A+</option>
          <option value="A">A</option>
          <option value="B">B</option>
        </select>

        <select
          className="text-xs border rounded px-2 py-1"
          multiple
          value={filters.type}
          onChange={(e) => setFilters(prev => ({
            ...prev,
            type: Array.from(e.target.selectedOptions, option => option.value as 'long' | 'short')
          }))}
        >
          <option value="long">Long</option>
          <option value="short">Short</option>
        </select>

        <select
          className="text-xs border rounded px-2 py-1"
          multiple
          value={filters.setupTypes}
          onChange={(e) => setFilters(prev => ({
            ...prev,
            setupTypes: Array.from(e.target.selectedOptions, option => option.value)
          }))}
        >
          <option value="pivot_bounce">Pivot Bounce</option>
          <option value="breakout">Breakout</option>
          <option value="support_confirmation">Support Confirmation</option>
        </select>

        <input
          type="number"
          min="1"
          step="0.1"
          value={filters.minRR}
          onChange={(e) => setFilters(prev => ({
            ...prev,
            minRR: parseFloat(e.target.value)
          }))}
          className="text-xs border rounded px-2 py-1 w-20"
          placeholder="Min RR"
        />
      </div>

      {/* Setup Cards */}
      <div className="grid gap-4">
        {filteredSetups.map((setup, index) => (
          <div 
            key={index}
            className={`
              p-3 rounded-lg shadow-sm border-l-4
              ${setup.type === 'long' 
                ? 'border-l-green-500 bg-green-50' 
                : 'border-l-red-500 bg-red-50'
              }
            `}
          >
            {/* Header */}
            <div className="flex justify-between items-start mb-2">
              <div>
                <span className={`
                  text-xs font-semibold px-2 py-1 rounded
                  ${setup.quality === 'A+' ? 'bg-purple-200 text-purple-800' :
                    setup.quality === 'A' ? 'bg-blue-200 text-blue-800' :
                    'bg-gray-200 text-gray-800'}
                `}>
                  {setup.quality}
                </span>
                <span className="ml-2 text-sm font-medium">
                  {setup.type.toUpperCase()} - {setup.subType.replace('_', ' ')}
                </span>
              </div>
              <div className="text-right">
                <span className="text-xs text-gray-500">{setup.timeframe}</span>
                <div className={`text-xs ${
                  setup.trendDirection === 'up' ? 'text-green-600' :
                  setup.trendDirection === 'down' ? 'text-red-600' :
                  'text-gray-600'
                }`}>
                  Trend: {setup.trendDirection}
                </div>
              </div>
            </div>

            {/* Main Info */}
            <div className="grid grid-cols-2 gap-2 mb-2 text-sm">
              <div>
                <div className="text-gray-600">Entry</div>
                <div className="font-medium">{setup.entry.toFixed(2)}</div>
              </div>
              <div>
                <div className="text-gray-600">Target</div>
                <div className="font-medium">{setup.target.toFixed(2)}</div>
              </div>
              <div>
                <div className="text-gray-600">Stop Loss</div>
                <div className="font-medium">{setup.stopLoss.toFixed(2)}</div>
              </div>
              <div>
                <div className="text-gray-600">R/R</div>
                <div className="font-medium">{setup.rr.toFixed(2)}</div>
              </div>
            </div>

            {/* Trailing Stop */}
            {setup.trailingStop && (
              <div className="mb-2 text-xs">
                <span className="text-gray-600">Trailing Stop @ 1R:</span>
                <span className="ml-1 font-medium">{setup.trailingStop.toFixed(2)}</span>
              </div>
            )}

            {/* Additional Info */}
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className="flex items-center">
                <div className={`w-2 h-2 rounded-full mr-1
                  ${setup.probability >= 60 ? 'bg-green-500' :
                    setup.probability >= 50 ? 'bg-yellow-500' : 'bg-red-500'}
                `} />
                <span>{setup.probability}% Prob</span>
              </div>
              <div>
                <span className={setup.volumeBuzz >= 50 ? 'text-green-600' : 'text-gray-600'}>
                  {setup.volumeBuzz}% Vol
                </span>
              </div>
              <div>
                <span className="text-gray-600">{setup.bestTime}</span>
              </div>
            </div>

            {/* Confirmations */}
            {setup.confirmations && (
              <div className="mt-2 flex flex-wrap gap-2">
                {Object.entries(setup.confirmations).map(([key, value]) => (
                  <span key={key} className={`
                    text-xs px-2 py-0.5 rounded
                    ${value ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}
                  `}>
                    {key.replace('_', ' ')}: {value ? '✓' : '✗'}
                  </span>
                ))}
              </div>
            )}

            {/* Indicators */}
            <div className="mt-2 flex gap-2">
              {setup.cluster && (
                <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded">
                  Cluster
                </span>
              )}
              {setup.divergence && (
                <span className="text-xs bg-purple-100 text-purple-800 px-2 py-0.5 rounded">
                  Divergence
                </span>
              )}
              {setup.repeatedTests > 1 && (
                <span className="text-xs bg-gray-100 text-gray-800 px-2 py-0.5 rounded">
                  {setup.repeatedTests}x Tested
                </span>
              )}
            </div>

            {/* Additional Targets */}
            {setup.additionalTargets?.length > 0 && (
              <div className="mt-2 text-xs text-gray-600">
                Additional Targets: {setup.additionalTargets.map(t => t?.toFixed(2)).join(', ')}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
