'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';

export default function SearchBar() {
  const [query, setQuery] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const symbol = query.toUpperCase().trim();
    setIsSubmitting(true);

    try {
      // Add to watchlist
      const response = await fetch('/api/watchlist', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ symbol }),
      });

      if (!response.ok) throw new Error('Failed to add to watchlist');
      
      toast.success(`${symbol} wurde zur Watchlist hinzugefügt`);

      // Navigate to chart view
      router.push(`/chart/${symbol}`);
      setQuery('');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Ein Fehler ist aufgetreten';
      toast.error(`Fehler beim Hinzufügen von ${symbol}: ${errorMessage}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <label htmlFor="search" className="sr-only">
        Symbol suchen
      </label>
      <div className="relative">
        <div className="pointer-events-none absolute inset-y-0 left-0 pl-3 flex items-center">
          <svg
            className={`h-5 w-5 ${isSubmitting ? 'text-blue-500' : 'text-gray-400'}`}
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
              clipRule="evenodd"
            />
          </svg>
        </div>
        <input
          type="text"
          name="search"
          id="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={isSubmitting}
          className={`
            block w-full bg-white border border-gray-300 rounded-md py-2 pl-10 pr-3 text-sm
            placeholder-gray-500 focus:outline-none focus:text-gray-900 focus:placeholder-gray-400
            focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm
            ${isSubmitting ? 'opacity-50 cursor-not-allowed' : ''}
          `}
          placeholder="Symbol suchen..."
        />
        {isSubmitting && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
            <LoadingSpinner size="sm" />
          </div>
        )}
      </div>
    </form>
  );
}
