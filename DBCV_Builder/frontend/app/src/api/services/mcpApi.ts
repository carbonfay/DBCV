import apiClient, { safeApiCall } from '@/api/axios';

export interface McpBuildRequest {
  prompt: string;
  context: Record<string, any>;
  bot_id: string;
}

export interface McpDraftRequest {
  prompt: string;
  context: Record<string, any>;
  bot_id: string;
}

export interface McpResponse {
  result: string;
  status: 'success' | 'error';
  message?: string;
}

const mcpApi = {
  build(data: McpBuildRequest) {
    return safeApiCall(apiClient.post('/mcp/build', data));
  },
  
  draft(data: McpDraftRequest) {
    return safeApiCall(apiClient.post('/mcp/draft', data));
  },
};

export default mcpApi;
