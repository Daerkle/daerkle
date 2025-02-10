'use client';

interface TimeframeSelectorProps {
  value: string;
  onChange: (timeframe: string) => void;
}

const timeframes = [
  { value: '1d', label: 'Tag' },
  { value: '1wk', label: 'Woche' },
  { value: '1mo', label: 'Monat' }
];

export default function TimeframeSelector({ value, onChange }: TimeframeSelectorProps) {
  return (
    <div className="inline-flex rounded-md shadow-sm" role="group">
      {timeframes.map((timeframe) => (
        <button
          key={timeframe.value}
          type="button"
          onClick={() => onChange(timeframe.value)}
          className={`
            px-4 py-2 text-sm font-medium
            ${timeframe.value === value
              ? 'bg-blue-600 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-50'
            }
            ${timeframe.value === timeframes[0].value && 'rounded-l-lg'}
            ${timeframe.value === timeframes[timeframes.length - 1].value && 'rounded-r-lg'}
            border border-gray-200
            focus:z-10 focus:ring-2 focus:ring-blue-500 focus:text-blue-700
          `}
        >
          {timeframe.label}
        </button>
      ))}
    </div>
  );
}
