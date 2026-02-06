/**
 * Graph List Component
 * =====================
 *
 * Displays a list of saved knowledge graphs with search and pagination
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { listGraphs, searchGraphs, deleteGraph, updateGraphVisibility } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { SkeletonGraphList } from './Skeleton';
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
  const [togglingVisibility, setTogglingVisibility] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { user, isAuthenticated } = useAuth();

  // Check if current user owns a graph
  const isOwner = (graph: Graph) => {
    return isAuthenticated && user && graph.user_id === user.id;
  };

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

  // Re-fetch graphs when auth state changes (login/logout)
  useEffect(() => {
    loadGraphs();
  }, [loadGraphs, refreshTrigger, isAuthenticated]);

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

  const handleToggleVisibility = async (graph: Graph, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!isOwner(graph)) return;

    try {
      setTogglingVisibility(graph.id);
      await updateGraphVisibility(graph.id, !graph.is_public);
      await loadGraphs(); // Refresh list
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update visibility');
    } finally {
      setTogglingVisibility(null);
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
            border: '1px solid var(--input-border)',
            borderRadius: '0.375rem',
            fontSize: '1rem',
            backgroundColor: 'var(--input-bg)',
            color: 'var(--text-primary)',
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
            backgroundColor: 'var(--error-bg)',
            border: '1px solid var(--error-border)',
            borderRadius: '0.375rem',
            color: 'var(--error-text)',
          }}
        >
          {error}
        </div>
      )}

      {/* Count */}
      <p style={{ marginBottom: '1rem', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
        {loading ? 'Loading graphs...' : `${total} graph${total !== 1 ? 's' : ''} found`}
      </p>

      {/* Skeleton Loading State */}
      {loading && <SkeletonGraphList count={3} />}

      {/* Empty State */}
      {!loading && graphs.length === 0 && (
        <div
          style={{
            textAlign: 'center',
            padding: '3rem',
            backgroundColor: 'var(--bg-tertiary)',
            borderRadius: '0.5rem',
            color: 'var(--text-muted)',
          }}
        >
          <p>No graphs found.</p>
          <p style={{ marginTop: '0.5rem', fontSize: '0.875rem' }}>
            Create your first graph using the form above.
          </p>
        </div>
      )}

      {/* Graph List */}
      {!loading && graphs.length > 0 && (
        <div style={{ display: 'grid', gap: '1rem' }}>
          {graphs.map((graph) => (
            <div
              key={graph.id}
              onClick={() => onSelectGraph(graph)}
              style={{
                padding: '1rem',
                border: '1px solid var(--border-color)',
                borderRadius: '0.5rem',
                cursor: 'pointer',
                transition: 'all 0.2s',
                backgroundColor: 'var(--bg-secondary)',
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)';
                e.currentTarget.style.borderColor = 'var(--accent-primary)';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.backgroundColor = 'var(--bg-secondary)';
                e.currentTarget.style.borderColor = 'var(--border-color)';
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <h3 style={{ margin: 0, fontSize: '1.125rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                      {graph.title || 'Untitled Graph'}
                    </h3>
                    {/* Visibility Badge */}
                    <span
                      style={{
                        padding: '0.125rem 0.5rem',
                        borderRadius: '9999px',
                        fontSize: '0.625rem',
                        fontWeight: '500',
                        textTransform: 'uppercase',
                        backgroundColor: graph.is_public ? 'var(--success-bg)' : 'var(--bg-tertiary)',
                        color: graph.is_public ? 'var(--success-text)' : 'var(--text-muted)',
                        border: `1px solid ${graph.is_public ? 'var(--success-border)' : 'var(--border-color)'}`,
                      }}
                    >
                      {graph.is_public ? 'Public' : 'Private'}
                    </span>
                  </div>
                  <p style={{ margin: '0 0 0.5rem 0', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                    {graph.source_text.substring(0, 150)}
                    {graph.source_text.length > 150 ? '...' : ''}
                  </p>
                  <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem', color: 'var(--text-light)' }}>
                    <span>{graph.nodes.length} nodes</span>
                    <span>{graph.edges.length} edges</span>
                    <span>{new Date(graph.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
                {/* Action buttons - only for owner */}
                {isOwner(graph) && (
                  <div style={{ display: 'flex', gap: '0.5rem', marginLeft: '1rem' }}>
                    {/* Toggle Visibility Button */}
                    <button
                      onClick={(e) => handleToggleVisibility(graph, e)}
                      disabled={togglingVisibility === graph.id}
                      style={{
                        padding: '0.5rem 0.75rem',
                        backgroundColor: 'var(--bg-tertiary)',
                        color: 'var(--text-secondary)',
                        border: '1px solid var(--border-color)',
                        borderRadius: '0.375rem',
                        fontSize: '0.75rem',
                        cursor: togglingVisibility === graph.id ? 'not-allowed' : 'pointer',
                        opacity: togglingVisibility === graph.id ? 0.6 : 1,
                      }}
                      title={graph.is_public ? 'Make private' : 'Make public'}
                    >
                      {togglingVisibility === graph.id ? '...' : (graph.is_public ? 'Make Private' : 'Make Public')}
                    </button>
                    {/* Delete Button */}
                    <button
                      onClick={(e) => handleDeleteClick(graph, e)}
                      style={{
                        padding: '0.5rem 0.75rem',
                        backgroundColor: 'var(--error-bg)',
                        color: 'var(--error-text)',
                        border: 'none',
                        borderRadius: '0.375rem',
                        fontSize: '0.75rem',
                        cursor: 'pointer',
                      }}
                      onMouseOver={(e) => {
                        e.currentTarget.style.backgroundColor = 'var(--error-border)';
                      }}
                      onMouseOut={(e) => {
                        e.currentTarget.style.backgroundColor = 'var(--error-bg)';
                      }}
                    >
                      Delete
                    </button>
                  </div>
                )}
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
              backgroundColor: 'var(--bg-secondary)',
              borderRadius: '0.5rem',
              padding: '1.5rem',
              maxWidth: '400px',
              width: '90%',
              boxShadow: '0 4px 6px var(--shadow-color)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.125rem', color: 'var(--text-primary)' }}>Delete Graph</h3>
            <p style={{ margin: '0 0 1.5rem 0', color: 'var(--text-muted)' }}>
              Are you sure you want to delete "{deleteConfirm.title}"? This action cannot be undone.
            </p>
            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setDeleteConfirm(null)}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: 'var(--btn-secondary-bg)',
                  color: 'var(--btn-secondary-text)',
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
