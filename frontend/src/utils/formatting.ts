// Format duration in milliseconds to human-readable string
export function formatDuration(ms: number): string {
  if (ms < 1000) {
    return `${ms}ms`;
  }
  return `${(ms / 1000).toFixed(2)}s`;
}

// Format SQL for display
export function formatSQL(sql: string): string {
  return sql
    .replace(/\s+/g, ' ')
    .trim();
}

// Truncate text to specified length
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

// Get badge color based on service type
export function getServiceBadgeColor(serviceId: string): string {
  const colors: Record<string, string> = {
    simple: 'bg-gray-100 text-gray-800',
    advanced: 'bg-blue-100 text-blue-800',
    chat: 'bg-green-100 text-green-800',
    agentic: 'bg-purple-100 text-purple-800',
  };
  return colors[serviceId] || 'bg-gray-100 text-gray-800';
}

// Format table data for display
export function formatTableValue(value: any): string {
  if (value === null || value === undefined) {
    return 'NULL';
  }
  if (typeof value === 'object') {
    return JSON.stringify(value);
  }
  return String(value);
}
