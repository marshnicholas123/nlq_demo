import { useState } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { clearChatHistory } from '@/api/text2sql';

interface SessionManagerProps {
  sessionId: string;
  onSessionChange: (newSessionId: string) => void;
  hasStatefulServices: boolean;
}

export default function SessionManager({
  sessionId,
  onSessionChange,
  hasStatefulServices,
}: SessionManagerProps) {
  const [isClearing, setIsClearing] = useState(false);

  const handleNewSession = () => {
    const newSessionId = uuidv4();
    onSessionChange(newSessionId);
  };

  const handleClearHistory = async () => {
    if (!confirm('Are you sure you want to clear the conversation history?')) {
      return;
    }

    setIsClearing(true);
    try {
      await clearChatHistory(sessionId);
      alert('Chat history cleared successfully!');
    } catch (error) {
      console.error('Error clearing history:', error);
      alert('Failed to clear history. Please try again.');
    } finally {
      setIsClearing(false);
    }
  };

  if (!hasStatefulServices) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-3">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Session Management</h3>

      <div className="space-y-3">
        <div>
          <label className="block text-xs text-gray-600 mb-1">Session ID</label>
          <div className="relative group">
            <input
              type="text"
              value={sessionId}
              readOnly
              className="w-full px-2 py-1.5 text-xs bg-gray-50 border border-gray-300 rounded font-mono text-gray-700 truncate pr-16"
              title={sessionId}
            />
            <button
              onClick={() => navigator.clipboard.writeText(sessionId)}
              className="absolute right-1 top-1/2 -translate-y-1/2 px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 rounded transition-colors"
              title="Copy session ID"
            >
              Copy
            </button>
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <button
            onClick={handleNewSession}
            className="w-full px-3 py-2 bg-primary-600 hover:bg-primary-700 text-white text-sm font-medium rounded transition-colors"
          >
            New Session
          </button>

          <button
            onClick={handleClearHistory}
            disabled={isClearing}
            className="w-full px-3 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white text-sm font-medium rounded transition-colors"
          >
            {isClearing ? 'Clearing...' : 'Clear History'}
          </button>
        </div>
      </div>

      <p className="mt-3 text-xs text-gray-500 leading-relaxed">
        Session ID is used for Chat and Agentic services to maintain conversation context
      </p>
    </div>
  );
}
