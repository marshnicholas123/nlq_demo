// Request types
export interface Text2SQLRequest {
  query: string;
  execute: boolean;
}

export interface ChatText2SQLRequest extends Text2SQLRequest {
  session_id: string;
}

export interface AgenticText2SQLRequest extends Text2SQLRequest {
  session_id: string;
  max_iterations: number;
}

// Response types
export interface ExecutionResult {
  success: boolean;
  data?: Array<Record<string, any>>;
  row_count?: number;
  error?: string;
}

export interface ValidationResult {
  query_executed: boolean;
  has_results: boolean;
  error_present: boolean;
  overall_valid: boolean;
}

export interface AgenticContextUsed {
  schema: boolean;
  metadata_rules: number;
  sample_tables: string[];
}

export interface RetrievalStats {
  vector_results?: number;
  bm25_results?: number;
  final_top_k?: number;
}

export interface Text2SQLResponse {
  sql: string;
  method: string;
  session_id?: string;
  resolved_query?: string;
  context_used?: string[];
  agentic_context?: AgenticContextUsed;
  iterations?: number;
  tool_calls?: number;
  execution_result?: ExecutionResult;
  validation_result?: ValidationResult;
  parsed_response?: string;
  retrieval_stats?: RetrievalStats;
  needs_clarification?: boolean;
  clarification_questions?: string[];
}

// Service configuration
export interface ServiceConfig {
  id: 'simple' | 'advanced' | 'chat' | 'agentic';
  name: string;
  description: string;
  endpoint: string;
  requiresSession: boolean;
  supportsFollowUp: boolean;
}

// Service result with metadata
export interface ServiceResult extends Text2SQLResponse {
  serviceId: string;
  serviceName: string;
  startTime: number;
  endTime: number;
  duration: number;
  error?: string;
}

// Clarification response
export interface ClarificationResponse {
  needs_clarification: boolean;
  questions: string[];
}
