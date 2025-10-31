import { ServiceResult } from '@/types/text2sql';
import { formatDuration, getServiceBadgeColor, formatTableValue } from '@/utils/formatting';
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

interface ServiceResultCardProps {
  result: ServiceResult;
}

export default function ServiceResultCard({ result }: ServiceResultCardProps) {
  const [showFullSQL, setShowFullSQL] = useState(false);
  const [activeTab, setActiveTab] = useState<'sql' | 'data' | 'metadata'>('sql');

  const hasError = !!result.error;
  const hasData = result.execution_result?.data && result.execution_result.data.length > 0;
  const needsClarification = result.needs_clarification && result.clarification_questions && result.clarification_questions.length > 0;

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getServiceBadgeColor(result.serviceId)}`}>
              {result.serviceName}
            </span>
            <span className="text-xs text-gray-500">
              {formatDuration(result.duration)}
            </span>
          </div>
          {hasError ? (
            <span className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded-full">
              ❌ Error
            </span>
          ) : needsClarification ? (
            <span className="text-xs px-2 py-1 bg-amber-100 text-amber-700 rounded-full">
              ❓ Needs Clarification
            </span>
          ) : (
            <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded-full">
              ✓ Success
            </span>
          )}
        </div>
      </div>

      {/* Clarification Request */}
      {needsClarification && (
        <div className="px-4 py-4 bg-amber-50 border-b border-amber-200">
          <div className="flex items-start gap-3">
            <div className="text-3xl">🤖</div>
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-amber-900 mb-2">
                Agent needs clarification to proceed
              </h4>
              <p className="text-sm text-amber-800 mb-3">
                The query is ambiguous or lacks sufficient context. Please provide more details:
              </p>
              <ul className="space-y-2">
                {result.clarification_questions!.map((question, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-amber-900">
                    <span className="font-semibold">{idx + 1}.</span>
                    <span>{question}</span>
                  </li>
                ))}
              </ul>
              <div className="mt-3 p-2 bg-amber-100 rounded text-xs text-amber-800">
                💡 <strong>Tip:</strong> Refine your query with more specific details and try again.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error Message */}
      {hasError && !needsClarification && (
        <div className="px-4 py-3 bg-red-50 border-b border-red-200">
          <p className="text-sm text-red-800">
            <span className="font-semibold">Error:</span> {result.error}
          </p>
        </div>
      )}

      {/* Tabs */}
      {!hasError && !needsClarification && (
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveTab('sql')}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === 'sql'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            SQL Query
          </button>
          {hasData && (
            <button
              onClick={() => setActiveTab('data')}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === 'data'
                  ? 'text-primary-600 border-b-2 border-primary-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Results ({result.execution_result?.row_count})
            </button>
          )}
          <button
            onClick={() => setActiveTab('metadata')}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === 'metadata'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Metadata
          </button>
        </div>
      )}

      {/* Content */}
      <div className="p-4">
        {/* SQL Tab */}
        {activeTab === 'sql' && !hasError && !needsClarification && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-xs font-semibold text-gray-700">Generated SQL</h4>
              <button
                onClick={() => setShowFullSQL(!showFullSQL)}
                className="text-xs text-primary-600 hover:text-primary-700"
              >
                {showFullSQL ? 'Collapse' : 'Expand'}
              </button>
            </div>
            <pre className={`bg-gray-900 text-gray-100 p-3 rounded-md text-xs overflow-x-auto ${showFullSQL ? '' : 'max-h-32 overflow-y-auto'}`}>
              <code>{result.sql}</code>
            </pre>

            {result.parsed_response && (
              <div className="mt-4">
                <h4 className="text-xs font-semibold text-gray-700 mb-2">Natural Language Response</h4>
                <div className="bg-blue-50 border border-blue-200 rounded-md p-3 prose prose-sm max-w-none prose-headings:text-gray-900 prose-p:text-gray-800 prose-strong:text-gray-900 prose-code:text-gray-900 prose-pre:bg-gray-900 prose-pre:text-gray-100">
                  <ReactMarkdown>{result.parsed_response}</ReactMarkdown>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Data Tab */}
        {activeTab === 'data' && hasData && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-xs">
              <thead className="bg-gray-50">
                <tr>
                  {Object.keys(result.execution_result!.data![0]).map((column) => (
                    <th
                      key={column}
                      className="px-3 py-2 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider"
                    >
                      {column}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {result.execution_result!.data!.slice(0, 50).map((row, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    {Object.values(row).map((value, cellIdx) => (
                      <td key={cellIdx} className="px-3 py-2 whitespace-nowrap text-gray-900">
                        {formatTableValue(value)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            {result.execution_result!.data!.length > 50 && (
              <p className="text-xs text-gray-500 mt-2 text-center">
                Showing first 50 of {result.execution_result!.row_count} rows
              </p>
            )}
          </div>
        )}

        {/* Metadata Tab */}
        {activeTab === 'metadata' && !hasError && !needsClarification && (
          <div className="space-y-3">
            {result.resolved_query && (
              <div>
                <h4 className="text-xs font-semibold text-gray-700 mb-1">Resolved Query</h4>
                <p className="text-sm text-gray-800 bg-gray-50 p-2 rounded">{result.resolved_query}</p>
              </div>
            )}

            {result.context_used && result.context_used.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-gray-700 mb-1">Context Used</h4>
                <div className="flex flex-wrap gap-1">
                  {result.context_used.map((ctx, idx) => (
                    <span key={idx} className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                      {ctx}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {result.agentic_context && (
              <div>
                <h4 className="text-xs font-semibold text-gray-700 mb-1">Agentic Context</h4>
                <div className="bg-gray-50 p-2 rounded space-y-1 text-xs">
                  <p>Schema Retrieved: {result.agentic_context.schema ? '✓' : '✗'}</p>
                  <p>Metadata Rules: {result.agentic_context.metadata_rules}</p>
                  <p>Sample Tables: {result.agentic_context.sample_tables.join(', ') || 'None'}</p>
                </div>
              </div>
            )}

            {result.retrieval_stats && (
              <div>
                <h4 className="text-xs font-semibold text-gray-700 mb-1">Retrieval Stats</h4>
                <div className="bg-gray-50 p-2 rounded space-y-1 text-xs">
                  {result.retrieval_stats.vector_results !== undefined && (
                    <p>Vector Results: {result.retrieval_stats.vector_results}</p>
                  )}
                  {result.retrieval_stats.bm25_results !== undefined && (
                    <p>BM25 Results: {result.retrieval_stats.bm25_results}</p>
                  )}
                  {result.retrieval_stats.final_top_k !== undefined && (
                    <p>Final Top-K: {result.retrieval_stats.final_top_k}</p>
                  )}
                </div>
              </div>
            )}

            {result.iterations !== undefined && (
              <div>
                <h4 className="text-xs font-semibold text-gray-700 mb-1">Agent Stats</h4>
                <div className="bg-gray-50 p-2 rounded space-y-1 text-xs">
                  <p>Iterations: {result.iterations}</p>
                  {result.tool_calls !== undefined && <p>Tool Calls: {result.tool_calls}</p>}
                </div>
              </div>
            )}

            {result.validation_result && (
              <div>
                <h4 className="text-xs font-semibold text-gray-700 mb-1">Validation</h4>
                <div className="bg-gray-50 p-2 rounded space-y-1 text-xs">
                  <p>Query Executed: {result.validation_result.query_executed ? '✓' : '✗'}</p>
                  <p>Has Results: {result.validation_result.has_results ? '✓' : '✗'}</p>
                  <p>Overall Valid: {result.validation_result.overall_valid ? '✓' : '✗'}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
