'use client';

import { useState } from 'react';
import SetupList from '@/components/SetupList';

export default function SetupsPage() {
  const [symbol, setSymbol] = useState('');
  const [currentSymbol, setCurrentSymbol] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!symbol) return;
    setCurrentSymbol(symbol.toUpperCase());
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Trading Setups</h1>
      
      {/* Symbol Input */}
      <form onSubmit={handleSubmit} className="mb-8">
        <div className="flex gap-4">
          <input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            placeholder="Symbol eingeben (z.B. AAPL)"
            className="flex-1 max-w-xs px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Analysieren
          </button>
        </div>
      </form>

      {/* Setup List */}
      {currentSymbol && (
        <div>
          <h2 className="text-xl font-semibold mb-4">
            Setups für {currentSymbol}
          </h2>
          <SetupList symbol={currentSymbol} />
        </div>
      )}
    </div>
  );
}
