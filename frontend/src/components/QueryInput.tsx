import { useState } from 'react';

interface QueryInputProps {
  onSubmit: (query: string, execute: boolean) => void;
  isLoading: boolean;
  disabled: boolean;
}

export default function QueryInput({ onSubmit, isLoading, disabled }: QueryInputProps) {
  const [query, setQuery] = useState('');
  const [execute, setExecute] = useState(true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !disabled) {
      onSubmit(query, execute);
    }
  };

  const exampleQueries = [
    'How many nuclear power plants are operational?',
    'List all countries with nuclear power plants',
    'What is the total capacity of operational plants?',
    'Show me the newest operational nuclear power plant',
    'Which reactor type is most common?',
  ];

  const handleExampleClick = (exampleQuery: string) => {
    setQuery(exampleQuery);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Query Input</h3>

      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label htmlFor="query" className="block text-xs text-gray-600 mb-1">
            Natural Language Query
          </label>
          <textarea
            id="query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your question about nuclear power plants..."
            rows={3}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
            disabled={isLoading}
          />
        </div>

        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={execute}
              onChange={(e) => setExecute(e.target.checked)}
              className="h-4 w-4 text-primary-600 rounded focus:ring-primary-500"
              disabled={isLoading}
            />
            <span className="text-sm text-gray-700">Execute SQL queries</span>
          </label>

          <button
            type="submit"
            disabled={disabled || !query.trim() || isLoading}
            className="ml-auto px-6 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-400 text-white text-sm font-medium rounded-md transition-colors"
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Processing...
              </span>
            ) : (
              'Run Query'
            )}
          </button>
        </div>
      </form>

      {/* Example Queries */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <h4 className="text-xs font-semibold text-gray-600 mb-2">Example Queries</h4>
        <div className="flex flex-wrap gap-2">
          {exampleQueries.map((example, idx) => (
            <button
              key={idx}
              onClick={() => handleExampleClick(example)}
              disabled={isLoading}
              className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 disabled:bg-gray-50 text-gray-700 rounded-full transition-colors"
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
