/**
 * Graph List Component
 * =====================
 *
 * Displays a list of saved knowledge graphs with search and pagination
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
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
  const [deleteConfirm, setDeleteConfirm] = useState<{ id: string; title: string } | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

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

  const loadGraphs = useCallback(async () => {
    // Check if input was focused before loading
    const wasInputFocused = document.activeElement === inputRef.current;

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
      // Restore focus to input if it was focused before
      if (wasInputFocused && inputRef.current) {
        inputRef.current.focus();
      }
    }
  }, [searchQuery, searchMode]);

  useEffect(() => {
    loadGraphs();
  }, [loadGraphs, refreshTrigger]);

  const handleDeleteClick = (graph: Graph, e: React.MouseEvent) => {
    e.stopPropagation();
    setDeleteConfirm({ id: graph.id, title: graph.title || 'Untitled Graph' });
  };

  const handleDeleteConfirm = async () => {
    if (!deleteConfirm) return;

    try {
      await deleteGraph(deleteConfirm.id);
      setDeleteConfirm(null);
      await loadGraphs(); // Refresh list
    } catch (err: any) {
      setDeleteConfirm(null);
      if (err.response?.status === 401) {
        setError('Authentication required. Please login to delete graphs.');
      } else {
        setError(err.response?.data?.detail || 'Failed to delete graph');
      }
    }
  };

  return (
    <div>
      {/* Search - always visible */}
      <div style={{ marginBottom: '1.5rem' }}>
        <input
          ref={inputRef}
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

      {/* Count / Loading */}
      <p style={{ marginBottom: '1rem', color: '#6b7280', fontSize: '0.875rem' }}>
        {loading ? 'Searching...' : `${total} graph${total !== 1 ? 's' : ''} found`}
      </p>

      {/* List */}
      {!loading && graphs.length === 0 ? (
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
                  onClick={(e) => handleDeleteClick(graph, e)}
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

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={() => setDeleteConfirm(null)}
        >
          <div
            style={{
              backgroundColor: 'white',
              borderRadius: '0.5rem',
              padding: '1.5rem',
              maxWidth: '400px',
              width: '90%',
              boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.125rem' }}>Delete Graph</h3>
            <p style={{ margin: '0 0 1.5rem 0', color: '#6b7280' }}>
              Are you sure you want to delete "{deleteConfirm.title}"? This action cannot be undone.
            </p>
            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setDeleteConfirm(null)}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#f3f4f6',
                  color: '#374151',
                  border: 'none',
                  borderRadius: '0.375rem',
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteConfirm}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#dc2626',
                  color: 'white',
                  border: 'none',
                  borderRadius: '0.375rem',
                  cursor: 'pointer',
                }}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
