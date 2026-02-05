/**
 * Graph Creation Form
 * ====================
 *
 * Form for creating new knowledge graphs from text input
 */

import React, { useState } from 'react';
import type { CreateGraphRequest } from '../types';

interface GraphFormProps {
  onSubmit: (request: CreateGraphRequest) => Promise<void>;
  loading?: boolean;
}

export const GraphForm: React.FC<GraphFormProps> = ({ onSubmit, loading = false }) => {
  const [text, setText] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [isPublic, setIsPublic] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!text.trim()) {
      setError('Please enter some text to analyze');
      return;
    }

    try {
      const request: CreateGraphRequest = {
        text: text.trim(),
        ...(title.trim() && { title: title.trim() }),
        ...(description.trim() && { description: description.trim() }),
        is_public: isPublic,
      };

      await onSubmit(request);

      // Clear form on success
      setText('');
      setTitle('');
      setDescription('');
      setIsPublic(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to create graph');
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ marginBottom: '1rem' }}>
        <label
          htmlFor="title"
          style={{
            display: 'block',
            marginBottom: '0.5rem',
            fontWeight: '500',
            color: 'var(--text-secondary)',
          }}
        >
          Title (optional)
        </label>
        <input
          id="title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g., Python and Data Science"
          disabled={loading}
          style={{
            width: '100%',
            padding: '0.5rem',
            border: '1px solid var(--input-border)',
            borderRadius: '0.375rem',
            fontSize: '1rem',
            backgroundColor: 'var(--input-bg)',
            color: 'var(--text-primary)',
          }}
        />
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <label
          htmlFor="text"
          style={{
            display: 'block',
            marginBottom: '0.5rem',
            fontWeight: '500',
            color: 'var(--text-secondary)',
          }}
        >
          Text to analyze *
        </label>
        <textarea
          id="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Enter text to extract knowledge graph from..."
          required
          disabled={loading}
          rows={6}
          style={{
            width: '100%',
            padding: '0.5rem',
            border: '1px solid var(--input-border)',
            borderRadius: '0.375rem',
            fontSize: '1rem',
            fontFamily: 'inherit',
            resize: 'vertical',
            backgroundColor: 'var(--input-bg)',
            color: 'var(--text-primary)',
          }}
        />
        <p style={{ marginTop: '0.25rem', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
          {text.length} / 10,000 characters
        </p>
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <label
          htmlFor="description"
          style={{
            display: 'block',
            marginBottom: '0.5rem',
            fontWeight: '500',
            color: 'var(--text-secondary)',
          }}
        >
          Description (optional)
        </label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Add notes or context..."
          disabled={loading}
          rows={3}
          style={{
            width: '100%',
            padding: '0.5rem',
            border: '1px solid var(--input-border)',
            borderRadius: '0.375rem',
            fontSize: '1rem',
            fontFamily: 'inherit',
            resize: 'vertical',
            backgroundColor: 'var(--input-bg)',
            color: 'var(--text-primary)',
          }}
        />
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <label
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            cursor: 'pointer',
            color: 'var(--text-secondary)',
          }}
        >
          <input
            type="checkbox"
            checked={isPublic}
            onChange={(e) => setIsPublic(e.target.checked)}
            disabled={loading}
            style={{
              width: '1rem',
              height: '1rem',
              cursor: 'pointer',
            }}
          />
          <span style={{ fontWeight: '500' }}>Make this graph public</span>
        </label>
        <p style={{ marginTop: '0.25rem', fontSize: '0.875rem', color: 'var(--text-muted)', marginLeft: '1.5rem' }}>
          Public graphs are visible to everyone. Private graphs are only visible to you.
        </p>
      </div>

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

      <button
        type="submit"
        disabled={loading || !text.trim()}
        style={{
          padding: '0.75rem 1.5rem',
          backgroundColor: loading ? 'var(--text-light)' : 'var(--accent-primary)',
          color: 'white',
          border: 'none',
          borderRadius: '0.375rem',
          fontSize: '1rem',
          fontWeight: '500',
          cursor: loading ? 'not-allowed' : 'pointer',
          transition: 'background-color 0.2s',
        }}
        onMouseOver={(e) => {
          if (!loading && text.trim()) {
            e.currentTarget.style.backgroundColor = 'var(--accent-hover)';
          }
        }}
        onMouseOut={(e) => {
          if (!loading) {
            e.currentTarget.style.backgroundColor = 'var(--accent-primary)';
          }
        }}
      >
        {loading ? 'Creating Graph...' : 'Create Graph'}
      </button>
    </form>
  );
};
