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
