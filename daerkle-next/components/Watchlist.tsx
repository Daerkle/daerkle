'use client';

import { useState, useEffect } from 'react';
import { useSymbol } from '@/contexts/SymbolContext';
import { useSidebar } from '@/contexts/SidebarContext';
import LoadingSpinner from './LoadingSpinner';
import toast from 'react-hot-toast';

interface StockData {
  price: number;
  change: number;
  volume: number;
  volumeBuzz: number;
  symbol: string;
  name: string;
}

interface WatchlistItem {
  symbol: string;
  name: string;
  data?: StockData;
  loading?: boolean;
}

interface WatchlistProps {
  onSymbolSelect: (symbol: string) => void;
  selectedSymbol?: string;
}

export default function Watchlist({ onSymbolSelect, selectedSymbol }: WatchlistProps) {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [newSymbol, setNewSymbol] = useState('');
  const [loading, setLoading] = useState(false);
  const { close } = useSidebar();

  // Load saved symbols on mount (client-side only)
  useEffect(() => {
    const savedItems = localStorage.getItem('watchlist');
    if (savedItems) {
      setItems(JSON.parse(savedItems));
    }
  }, []);

  // Save changes to localStorage
  useEffect(() => {
    localStorage.setItem('watchlist', JSON.stringify(items));
  }, [items]);

  // Update stock data periodically
  useEffect(() => {
    const updateData = async () => {
      setItems(prevItems => 
        prevItems.map(item => ({ ...item, loading: true }))
      );

      const updatedItems = await Promise.all(
        items.map(async (item) => {
          try {
            const response = await fetch(`http://localhost:8000/api/stock-data?symbol=${item.symbol}`);
            if (!response.ok) throw new Error('Failed to fetch');
            
            const rawData = await response.json();
            const lastBar = rawData[rawData.length - 1];
            const prevBar = rawData[rawData.length - 2];
            const change = ((lastBar.close - prevBar.close) / prevBar.close) * 100;

            return {
              ...item,
              loading: false,
              data: {
                price: lastBar.close,
                change: change,
                volume: lastBar.volume,
                volumeBuzz: lastBar.volumeBuzz,
                symbol: item.symbol,
                name: item.symbol
              }
            };
          } catch (error) {
            console.error(`Error updating ${item.symbol}:`, error);
            return { ...item, loading: false };
          }
        })
      );

      setItems(updatedItems);
    };

    updateData();
    const interval = setInterval(updateData, 30000);
    return () => clearInterval(interval);
  }, [items.length]);

  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSymbol || items.some(item => item.symbol === newSymbol)) {
      return;
    }

    setItems(prev => [...prev, { 
      symbol: newSymbol, 
      name: newSymbol,
      loading: true 
    }]);
    setNewSymbol('');
  };

  const handleRemove = (symbol: string) => {
    setItems(prev => prev.filter(item => item.symbol !== symbol));
  };

  const handleSelect = (symbol: string) => {
    onSymbolSelect(symbol);
    close();
  };

  return (
    <div className="h-full flex flex-col">
      <div className="text-sm font-semibold mb-2 pb-2 border-b">Watchlist</div>

      <form onSubmit={handleAdd} className="relative mb-2">
        <input
          type="text"
          value={newSymbol}
          onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
          placeholder="Symbol hinzufügen..."
          className="w-full px-2 py-1 pr-8 text-xs border rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        <button
          type="submit"
          disabled={!newSymbol}
          className={`absolute right-1 top-1/2 -translate-y-1/2 px-1.5 text-xs rounded
            ${newSymbol 
              ? 'text-blue-500 hover:text-blue-600' 
              : 'text-gray-300'
            } transition-colors`}
        >
          +
        </button>
      </form>

      <div className="flex-1 overflow-auto space-y-1">
        {items.map((item) => (
          <div
            key={item.symbol}
            className={`
              relative group p-2 rounded cursor-pointer
              ${selectedSymbol === item.symbol 
                ? 'bg-blue-50 border-blue-200' 
                : 'hover:bg-gray-50'
              }
            `}
            onClick={() => handleSelect(item.symbol)}
          >
            <div className="flex justify-between items-start">
              <div>
                <div className="text-sm font-medium">{item.symbol}</div>
                <div className="text-xs text-gray-500">{item.data?.name || item.name}</div>
              </div>
              
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleRemove(item.symbol);
                }}
                className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-opacity"
              >
                ×
              </button>
            </div>

            {item.data && (
              <div className="mt-1 grid grid-cols-2 gap-x-2 text-xs">
                <div>
                  <span className={item.data.change >= 0 ? 'text-green-600' : 'text-red-600'}>
                    ${item.data.price.toFixed(2)}
                  </span>
                </div>
                <div className="text-right">
                  <span className={item.data.change >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {item.data.change >= 0 ? '+' : ''}{item.data.change.toFixed(2)}%
                  </span>
                </div>
                <div className="text-gray-600">
                  Vol: {(item.data.volume / 1000000).toFixed(1)}M
                </div>
                <div className="text-right">
                  {item.data?.volumeBuzz !== undefined ? (
                    <span className={item.data.volumeBuzz >= 50 ? 'text-green-600' : 'text-gray-600'}>
                      {item.data.volumeBuzz.toFixed(1)}% Buzz
                    </span>
                  ) : (
                    <span className="text-gray-600">-</span>
                  )}
                </div>
              </div>
            )}

            {item.loading && (
              <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center">
                <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
              </div>
            )}
          </div>
        ))}

        {items.length === 0 && (
          <div className="text-gray-500 text-xs text-center py-4">
            Keine Symbole in der Watchlist
          </div>
        )}
      </div>
    </div>
  );
}
