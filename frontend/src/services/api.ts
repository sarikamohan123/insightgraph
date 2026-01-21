/**
 * API Client Service
 * ===================
 *
 * Axios-based client for communicating with the InsightGraph backend API
 */

import axios from 'axios';
import type {
  ExtractResponse,
  Graph,
  GraphListResponse,
  CreateGraphRequest,
  SearchMode,
  SemanticSearchResponse,
  User,
  Token,
  RegisterRequest,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API Key management
let apiKey: string | null = null;

export const setApiKey = (key: string) => {
  apiKey = key;
  localStorage.setItem('insightgraph_api_key', key);
};

export const getApiKey = (): string | null => {
  if (!apiKey) {
    apiKey = localStorage.getItem('insightgraph_api_key');
  }
  return apiKey;
};

export const clearApiKey = () => {
  apiKey = null;
  localStorage.removeItem('insightgraph_api_key');
};

// Add API key to requests if available
apiClient.interceptors.request.use((config) => {
  const key = getApiKey();
  if (key) {
    config.headers['X-API-Key'] = key;
  }
  return config;
});

/**
 * Extract entities and relationships from text (in-memory, not saved)
 */
export const extractGraph = async (text: string): Promise<ExtractResponse> => {
  const response = await apiClient.post<ExtractResponse>('/extract', { text });
  return response.data;
};

/**
 * Create and save a knowledge graph to database
 */
export const createGraph = async (request: CreateGraphRequest): Promise<Graph> => {
  const response = await apiClient.post<Graph>('/graphs', request);
  return response.data;
};

/**
 * List all saved graphs with pagination
 */
export const listGraphs = async (
  limit: number = 50,
  offset: number = 0
): Promise<GraphListResponse> => {
  const response = await apiClient.get<GraphListResponse>('/graphs', {
    params: { limit, offset },
  });
  return response.data;
};

/**
 * Get a specific graph by ID
 */
export const getGraph = async (id: string): Promise<Graph> => {
  const response = await apiClient.get<Graph>(`/graphs/${id}`);
  return response.data;
};

/**
 * Delete a graph
 */
export const deleteGraph = async (id: string): Promise<void> => {
  await apiClient.delete(`/graphs/${id}`);
};

/**
 * Search graphs by text content (keyword or semantic)
 */
export const searchGraphs = async (
  query: string,
  limit: number = 20,
  mode: SearchMode = 'keyword'
): Promise<GraphListResponse> => {
  const response = await apiClient.get<GraphListResponse>('/graphs/search/', {
    params: { q: query, limit, mode },
  });
  return response.data;
};

/**
 * Semantic search with similarity scores
 */
export const semanticSearchGraphs = async (
  query: string,
  limit: number = 20,
  threshold: number = 0.5
): Promise<SemanticSearchResponse> => {
  const response = await apiClient.get<SemanticSearchResponse>('/graphs/search/semantic', {
    params: { q: query, limit, threshold },
  });
  return response.data;
};

/**
 * Get system stats
 */
export const getStats = async (): Promise<any> => {
  const response = await apiClient.get('/stats');
  return response.data;
};

/**
 * Health check
 */
export const healthCheck = async (): Promise<{ status: string; extractor: string }> => {
  const response = await apiClient.get('/health');
  return response.data;
};

// =========================================================================
// Authentication API (Phase 6)
// =========================================================================

// JWT token management
let jwtToken: string | null = null;

export const setJwtToken = (token: string | null) => {
  jwtToken = token;
  if (token) {
    localStorage.setItem('insightgraph_jwt', token);
  } else {
    localStorage.removeItem('insightgraph_jwt');
  }
};

export const getJwtToken = (): string | null => {
  if (!jwtToken) {
    jwtToken = localStorage.getItem('insightgraph_jwt');
  }
  return jwtToken;
};

// Add JWT token to requests if available
apiClient.interceptors.request.use((config) => {
  const token = getJwtToken();
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  return config;
});

/**
 * Register a new user
 */
export const register = async (data: RegisterRequest): Promise<User> => {
  const response = await apiClient.post<User>('/auth/register', data);
  return response.data;
};

/**
 * Login and get JWT token
 */
export const login = async (email: string, password: string): Promise<Token> => {
  // OAuth2 uses form data with "username" field (which is actually email)
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);

  const response = await apiClient.post<Token>('/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });

  // Store the token
  setJwtToken(response.data.access_token);
  return response.data;
};

/**
 * Get current user profile
 */
export const getCurrentUser = async (): Promise<User> => {
  const response = await apiClient.get<User>('/auth/me');
  return response.data;
};

/**
 * Logout - clear stored token
 */
export const logout = () => {
  setJwtToken(null);
};
