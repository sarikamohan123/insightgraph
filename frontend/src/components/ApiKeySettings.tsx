/**
 * API Key Settings Component
 * ===========================
 *
 * Allows users to configure their API key for authenticated requests
 */

import React, { useState, useEffect } from 'react';
import { getApiKey, setApiKey, clearApiKey } from '../services/api';

export const ApiKeySettings: React.FC = () => {
  const [apiKey, setLocalApiKey] = useState('');
  const [isSet, setIsSet] = useState(false);
  const [showKey, setShowKey] = useState(false);

  useEffect(() => {
    const key = getApiKey();
    if (key) {
      setLocalApiKey(key);
      setIsSet(true);
    }
  }, []);

  const handleSave = () => {
    if (apiKey.trim()) {
      setApiKey(apiKey.trim());
      setIsSet(true);
      alert('API key saved!');
    }
  };

  const handleClear = () => {
    clearApiKey();
    setLocalApiKey('');
    setIsSet(false);
    alert('API key cleared!');
  };

  return (
    <div style={{
      marginBottom: '1.5rem',
      padding: '1rem',
      backgroundColor: '#f9fafb',
      borderRadius: '0.5rem',
      border: '1px solid #e5e7eb',
    }}>
      <h3 style={{ margin: '0 0 0.75rem 0', fontSize: '1rem', fontWeight: '600' }}>
        API Key Settings
      </h3>
      <p style={{ margin: '0 0 0.75rem 0', fontSize: '0.875rem', color: '#6b7280' }}>
        {isSet
          ? '✓ API key is configured. You can create and delete graphs.'
          : 'Set your API key to create and delete graphs. Leave empty for read-only access.'}
      </p>
      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        <input
          type={showKey ? 'text' : 'password'}
          value={apiKey}
          onChange={(e) => setLocalApiKey(e.target.value)}
          placeholder="Enter your API key"
          style={{
            flex: 1,
            padding: '0.5rem',
            border: '1px solid #d1d5db',
            borderRadius: '0.375rem',
            fontSize: '0.875rem',
          }}
        />
        <button
          onClick={() => setShowKey(!showKey)}
          style={{
            padding: '0.5rem 0.75rem',
            backgroundColor: 'white',
            border: '1px solid #d1d5db',
            borderRadius: '0.375rem',
            fontSize: '0.875rem',
            cursor: 'pointer',
          }}
        >
          {showKey ? 'Hide' : 'Show'}
        </button>
        <button
          onClick={handleSave}
          disabled={!apiKey.trim()}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: apiKey.trim() ? '#3b82f6' : '#9ca3af',
            color: 'white',
            border: 'none',
            borderRadius: '0.375rem',
            fontSize: '0.875rem',
            cursor: apiKey.trim() ? 'pointer' : 'not-allowed',
          }}
        >
          Save
        </button>
        {isSet && (
          <button
            onClick={handleClear}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#fee2e2',
              color: '#991b1b',
              border: 'none',
              borderRadius: '0.375rem',
              fontSize: '0.875rem',
              cursor: 'pointer',
            }}
          >
            Clear
          </button>
        )}
      </div>
    </div>
  );
};
