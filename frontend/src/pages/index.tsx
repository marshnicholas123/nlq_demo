import { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import Head from 'next/head';
import SessionManager from '@/components/SessionManager';
import ServiceToggle from '@/components/ServiceToggle';
import QueryInput from '@/components/QueryInput';
import ServiceResultCard from '@/components/ServiceResultCard';
import { ServiceResult } from '@/types/text2sql';
import { callService, SERVICES } from '@/api/text2sql';

export default function DemoComparison() {
  const [sessionId, setSessionId] = useState<string>('');
  const [selectedServices, setSelectedServices] = useState<string[]>([]);
  const [results, setResults] = useState<ServiceResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentQuery, setCurrentQuery] = useState<string>('');
  const [currentRunningService, setCurrentRunningService] = useState<string>('');
  const [completedCount, setCompletedCount] = useState(0);

  // Initialize session ID and select all services on mount
  useEffect(() => {
    setSessionId(uuidv4());
    setSelectedServices(SERVICES.map((s) => s.id));
  }, []);

  const handleServiceToggle = (serviceId: string) => {
    setSelectedServices((prev) =>
      prev.includes(serviceId)
        ? prev.filter((id) => id !== serviceId)
        : [...prev, serviceId]
    );
  };

  const handleToggleAll = (selected: boolean) => {
    setSelectedServices(selected ? SERVICES.map((s) => s.id) : []);
  };

  const handleSessionChange = (newSessionId: string) => {
    setSessionId(newSessionId);
    // Optionally clear results when session changes
    setResults([]);
  };

  const handleQuerySubmit = async (query: string, execute: boolean) => {
    if (selectedServices.length === 0) {
      alert('Please select at least one service');
      return;
    }

    setIsLoading(true);
    setCurrentQuery(query);
    setResults([]);
    setCompletedCount(0);

    // Run services sequentially one at a time
    for (let i = 0; i < selectedServices.length; i++) {
      const serviceId = selectedServices[i];
      const service = SERVICES.find((s) => s.id === serviceId)!;

      // Update progress indicator
      setCurrentRunningService(service.name);
      setCompletedCount(i);

      const startTime = Date.now();

      try {
        const response = await callService(
          serviceId,
          query,
          execute,
          service.requiresSession ? sessionId : undefined
        );

        const endTime = Date.now();

        const result: ServiceResult = {
          ...response,
          serviceId,
          serviceName: service.name,
          startTime,
          endTime,
          duration: endTime - startTime,
        };

        // Add result immediately after completion
        setResults((prev) => [...prev, result]);

      } catch (error: any) {
        const endTime = Date.now();

        // Create error result
        const errorResult: ServiceResult = {
          serviceId,
          serviceName: service.name,
          startTime,
          endTime,
          duration: endTime - startTime,
          sql: '',
          method: service.id,
          error: error.message || 'Unknown error occurred',
        };

        // Add error result immediately
        setResults((prev) => [...prev, errorResult]);
      }
    }

    // All services completed
    setIsLoading(false);
    setCurrentRunningService('');
    setCompletedCount(selectedServices.length);
  };

  const hasStatefulServices = selectedServices.some((id) => {
    const service = SERVICES.find((s) => s.id === id);
    return service?.requiresSession;
  });

  return (
    <>
      <Head>
        <title>Text2SQL Demo - Service Comparison</title>
        <meta name="description" content="Compare different Text2SQL service approaches" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div className="flex flex-col h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b border-gray-200 flex-shrink-0">
          <div className="px-4 py-4 lg:px-6">
            <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">
              Text2SQL Service Comparison Demo
            </h1>
            <p className="mt-1 text-xs lg:text-sm text-gray-600">
              Compare different Text2SQL approaches side-by-side with the same query
            </p>
          </div>
        </header>

        {/* Main Layout - Two Column */}
        <div className="flex flex-1 overflow-hidden">
          {/* Left Sidebar */}
          <aside className="w-full lg:w-80 xl:w-96 bg-gray-50 border-r border-gray-200 overflow-y-auto flex-shrink-0">
            <div className="p-4 space-y-4">
              {/* Session Manager */}
              <SessionManager
                sessionId={sessionId}
                onSessionChange={handleSessionChange}
                hasStatefulServices={hasStatefulServices}
              />

              {/* Service Selection */}
              <ServiceToggle
                selectedServices={selectedServices}
                onToggle={handleServiceToggle}
                onToggleAll={handleToggleAll}
              />
            </div>
          </aside>

          {/* Main Content Area */}
          <main className="flex-1 overflow-y-auto">
            <div className="p-4 lg:p-6 max-w-7xl mx-auto">
              {/* Query Input */}
              <QueryInput
                onSubmit={handleQuerySubmit}
                isLoading={isLoading}
                disabled={selectedServices.length === 0}
              />

              {/* Current Query Display */}
              {currentQuery && results.length > 0 && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                  <h3 className="text-sm font-semibold text-blue-900 mb-1">Current Query</h3>
                  <p className="text-sm text-blue-800">{currentQuery}</p>
                </div>
              )}

              {/* Results Grid */}
              {results.length > 0 && (
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-bold text-gray-900">Results</h2>
                    <button
                      onClick={() => setResults([])}
                      className="px-4 py-2 text-sm bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-md transition-colors"
                    >
                      Clear Results
                    </button>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {results.map((result) => (
                      <ServiceResultCard key={result.serviceId} result={result} />
                    ))}
                  </div>
                </div>
              )}

              {/* Progress Indicator - Shows while loading */}
              {isLoading && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
                  <div className="flex items-center gap-4 mb-4">
                    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-600 flex-shrink-0"></div>
                    <div className="flex-1">
                      <h3 className="text-base font-semibold text-gray-900 mb-1">
                        Running: {currentRunningService}
                      </h3>
                      <p className="text-sm text-gray-600">
                        Progress: {completedCount} / {selectedServices.length} completed
                      </p>
                    </div>
                  </div>

                  {/* Progress bar */}
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${(completedCount / selectedServices.length) * 100}%` }}
                    ></div>
                  </div>

                  {/* Service list with status */}
                  <div className="mt-4 space-y-2">
                    {selectedServices.map((serviceId, index) => {
                      const service = SERVICES.find((s) => s.id === serviceId)!;
                      const isCompleted = index < completedCount;
                      const isCurrent = index === completedCount;
                      const isPending = index > completedCount;

                      return (
                        <div
                          key={serviceId}
                          className={`flex items-center gap-2 text-sm px-3 py-2 rounded ${
                            isCompleted ? 'bg-green-50 text-green-800' :
                            isCurrent ? 'bg-blue-50 text-blue-800 font-medium' :
                            'bg-gray-50 text-gray-500'
                          }`}
                        >
                          {isCompleted && <span className="text-green-600">✓</span>}
                          {isCurrent && <span className="animate-pulse">⚡</span>}
                          {isPending && <span className="text-gray-400">○</span>}
                          <span>{service.name}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Empty State */}
              {results.length === 0 && !isLoading && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
                  <div className="text-6xl mb-4">🔍</div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    No Results Yet
                  </h3>
                  <p className="text-sm text-gray-600">
                    Select services and enter a query to see how different approaches compare
                  </p>
                </div>
              )}
            </div>
          </main>
        </div>

        {/* Footer */}
        <footer className="bg-white border-t border-gray-200 flex-shrink-0">
          <div className="px-4 py-3">
            <p className="text-xs text-gray-600 text-center">
              Text2SQL Demo - Comparing Simple, Advanced, Chat, and Agentic approaches
            </p>
          </div>
        </footer>
      </div>
    </>
  );
}
