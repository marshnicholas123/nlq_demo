import {
  Text2SQLRequest,
  ChatText2SQLRequest,
  AgenticText2SQLRequest,
  Text2SQLResponse,
  ServiceConfig,
} from '@/types/text2sql';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';

// Service configurations
export const SERVICES: ServiceConfig[] = [
  {
    id: 'simple',
    name: 'Simple',
    description: 'Basic schema-based SQL generation',
    endpoint: '/text2sql/simple',
    requiresSession: false,
    supportsFollowUp: false,
  },
  {
    id: 'advanced',
    name: 'Advanced',
    description: 'Hybrid retrieval with BM25 + Vector search',
    endpoint: '/text2sql/advanced',
    requiresSession: false,
    supportsFollowUp: false,
  },
  {
    id: 'chat',
    name: 'Chat',
    description: 'Conversational with history management',
    endpoint: '/text2sql/chat',
    requiresSession: true,
    supportsFollowUp: true,
  },
  {
    id: 'agentic',
    name: 'Agentic',
    description: 'LangGraph-based agent with tools and reflection',
    endpoint: '/text2sql/agentic',
    requiresSession: true,
    supportsFollowUp: true,
  },
];

// API client functions
export async function callSimpleService(
  request: Text2SQLRequest
): Promise<Text2SQLResponse> {
  const response = await fetch(`${API_BASE_URL}/text2sql/simple`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Failed to call simple service');
  }

  return response.json();
}

export async function callAdvancedService(
  request: Text2SQLRequest
): Promise<Text2SQLResponse> {
  const response = await fetch(`${API_BASE_URL}/text2sql/advanced`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Failed to call advanced service');
  }

  return response.json();
}

export async function callChatService(
  request: ChatText2SQLRequest
): Promise<Text2SQLResponse> {
  const response = await fetch(`${API_BASE_URL}/text2sql/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Failed to call chat service');
  }

  return response.json();
}

export async function callAgenticService(
  request: AgenticText2SQLRequest
): Promise<Text2SQLResponse> {
  const response = await fetch(`${API_BASE_URL}/text2sql/agentic`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));

    // Handle clarification requests - return as a special response type instead of throwing
    if (response.status === 400 && error.detail?.needs_clarification) {
      return {
        sql: '',
        method: 'agentic',
        needs_clarification: true,
        clarification_questions: error.detail.questions || [],
      } as Text2SQLResponse;
    }

    throw new Error(error.detail || 'Failed to call agentic service');
  }

  return response.json();
}

export async function clearChatHistory(sessionId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/text2sql/chat/${sessionId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Failed to clear chat history');
  }
}

// Helper function to call the appropriate service
export async function callService(
  serviceId: string,
  query: string,
  execute: boolean,
  sessionId?: string,
  maxIterations: number = 3
): Promise<Text2SQLResponse> {
  const baseRequest: Text2SQLRequest = { query, execute };

  switch (serviceId) {
    case 'simple':
      return callSimpleService(baseRequest);

    case 'advanced':
      return callAdvancedService(baseRequest);

    case 'chat':
      if (!sessionId) throw new Error('Session ID required for chat service');
      return callChatService({ ...baseRequest, session_id: sessionId });

    case 'agentic':
      if (!sessionId) throw new Error('Session ID required for agentic service');
      return callAgenticService({
        ...baseRequest,
        session_id: sessionId,
        max_iterations: maxIterations,
      });

    default:
      throw new Error(`Unknown service: ${serviceId}`);
  }
}
