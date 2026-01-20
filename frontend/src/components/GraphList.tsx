/**
 * Graph List Component
 * =====================
 *
 * Displays a list of saved knowledge graphs with search and pagination
 */

import React, { useState, useEffect, useRef } from 'react';
import { listGraphs, searchGraphs, deleteGraph } from '../services/api';
import type { Graph, SearchMode } from '../types';

interface GraphListProps {
  onSelectGraph: (graph: Graph) => void;
  refreshTrigger?: number;
}

export const GraphList: React.FC<GraphListProps> = ({ onSelectGraph, refreshTrigger = 0 }) => {
  const [graphs, setGraphs] = useState<Graph[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [inputValue, setInputValue] = useState(''); // Immediate input value
  const [searchQuery, setSearchQuery] = useState(''); // Debounced search query
  const [searchMode, setSearchMode] = useState<SearchMode>('keyword');
  const [total, setTotal] = useState(0);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Debounce input changes - wait 300ms after user stops typing
  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    debounceRef.current = setTimeout(() => {
      setSearchQuery(inputValue);
    }, 300);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [inputValue]);

  const loadGraphs = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = searchQuery
        ? await searchGraphs(searchQuery, 20, searchMode)
        : await listGraphs(50, 0);

      setGraphs(response.graphs);
      setTotal(response.total);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load graphs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGraphs();
  }, [searchQuery, searchMode, refreshTrigger]);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();

    if (!confirm('Are you sure you want to delete this graph?')) {
      return;
    }

    try {
      await deleteGraph(id);
      await loadGraphs(); // Refresh list
    } catch (err: any) {
      if (err.response?.status === 401) {
        alert('Authentication required. Please set your API key.');
      } else {
        alert(err.response?.data?.detail || 'Failed to delete graph');
      }
    }
  };

  if (loading && graphs.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem', color: '#6b7280' }}>
        Loading graphs...
      </div>
    );
  }

  return (
    <div>
      {/* Search */}
      <div style={{ marginBottom: '1.5rem' }}>
        <input
          type="text"
          placeholder={searchMode === 'semantic' ? 'Search by meaning...' : 'Search graphs...'}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          style={{
            width: '100%',
            padding: '0.75rem',
            border: '1px solid #d1d5db',
            borderRadius: '0.375rem',
            fontSize: '1rem',
          }}
        />
        {/* Search Mode Toggle */}
        <div style={{ marginTop: '0.5rem', display: 'flex', gap: '1rem', fontSize: '0.875rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', cursor: 'pointer' }}>
            <input
              type="radio"
              name="searchMode"
              value="keyword"
              checked={searchMode === 'keyword'}
              onChange={() => setSearchMode('keyword')}
            />
            Keyword
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', cursor: 'pointer' }}>
            <input
              type="radio"
              name="searchMode"
              value="semantic"
              checked={searchMode === 'semantic'}
              onChange={() => setSearchMode('semantic')}
            />
            Semantic (AI)
          </label>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div
          style={{
            marginBottom: '1rem',
            padding: '0.75rem',
            backgroundColor: '#fee2e2',
            border: '1px solid #fecaca',
            borderRadius: '0.375rem',
            color: '#991b1b',
          }}
        >
          {error}
        </div>
      )}

      {/* Count */}
      <p style={{ marginBottom: '1rem', color: '#6b7280', fontSize: '0.875rem' }}>
        {total} graph{total !== 1 ? 's' : ''} found
      </p>

      {/* List */}
      {graphs.length === 0 ? (
        <div
          style={{
            textAlign: 'center',
            padding: '3rem',
            backgroundColor: '#f9fafb',
            borderRadius: '0.5rem',
            color: '#6b7280',
          }}
        >
          <p>No graphs found.</p>
          <p style={{ marginTop: '0.5rem', fontSize: '0.875rem' }}>
            Create your first graph using the form above.
          </p>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: '1rem' }}>
          {graphs.map((graph) => (
            <div
              key={graph.id}
              onClick={() => onSelectGraph(graph)}
              style={{
                padding: '1rem',
                border: '1px solid #e5e7eb',
                borderRadius: '0.5rem',
                cursor: 'pointer',
                transition: 'all 0.2s',
                backgroundColor: 'white',
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.backgroundColor = '#f9fafb';
                e.currentTarget.style.borderColor = '#3b82f6';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.backgroundColor = 'white';
                e.currentTarget.style.borderColor = '#e5e7eb';
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div style={{ flex: 1 }}>
                  <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.125rem', fontWeight: '600' }}>
                    {graph.title || 'Untitled Graph'}
                  </h3>
                  <p style={{ margin: '0 0 0.5rem 0', color: '#6b7280', fontSize: '0.875rem' }}>
                    {graph.source_text.substring(0, 150)}
                    {graph.source_text.length > 150 ? '...' : ''}
                  </p>
                  <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem', color: '#9ca3af' }}>
                    <span>{graph.nodes.length} nodes</span>
                    <span>{graph.edges.length} edges</span>
                    <span>{new Date(graph.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
                <button
                  onClick={(e) => handleDelete(graph.id, e)}
                  style={{
                    padding: '0.5rem 1rem',
                    backgroundColor: '#fee2e2',
                    color: '#991b1b',
                    border: 'none',
                    borderRadius: '0.375rem',
                    fontSize: '0.875rem',
                    cursor: 'pointer',
                    marginLeft: '1rem',
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.backgroundColor = '#fecaca';
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.backgroundColor = '#fee2e2';
                  }}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
