/**
 * TypeScript Type Definitions
 * ============================
 *
 * Type definitions matching the backend API responses
 */

export interface Node {
  id: string;
  label: string;
  type: string;
  confidence: number;
}

export interface Edge {
  source: string;
  target: string;
  relation: string;
}

export interface ExtractResponse {
  nodes: Node[];
  edges: Edge[];
}

export interface GraphNode {
  id: string;
  node_id: string;
  label: string;
  type: string;
  confidence: number;
}

export interface GraphEdge {
  id: string;
  source_node_id: string;
  target_node_id: string;
  relation: string;
}

export interface Graph {
  id: string;
  title: string | null;
  description: string | null;
  source_text: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  is_public: boolean;
  user_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface GraphListResponse {
  graphs: Graph[];
  total: number;
  limit: number;
  offset: number;
}

export interface CreateGraphRequest {
  text: string;
  title?: string;
  description?: string;
  is_public?: boolean;
}

// For react-force-graph
export interface ForceGraphNode {
  id: string;
  name: string;
  type: string;
  confidence?: number;
}

export interface ForceGraphLink {
  source: string;
  target: string;
  relation: string;
}

export interface ForceGraphData {
  nodes: ForceGraphNode[];
  links: ForceGraphLink[];
}

// =========================================================================
// Semantic Search Types (Phase 5)
// =========================================================================

export type SearchMode = 'keyword' | 'semantic';

export interface SemanticSearchResult {
  graph: Graph;
  similarity_score: number;
}

export interface SemanticSearchResponse {
  results: SemanticSearchResult[];
  total: number;
  query: string;
  search_mode: string;
}

// =========================================================================
// Authentication Types (Phase 6)
// =========================================================================

export interface User {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  created_at: string;
}

export interface LoginRequest {
  username: string; // Actually email, but OAuth2 spec uses "username"
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}
