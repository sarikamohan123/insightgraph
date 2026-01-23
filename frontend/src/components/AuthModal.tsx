/**
 * Authentication Modal Component
 * ===============================
 *
 * Modal for login and registration with tab switching.
 */

import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose }) => {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);

  const { login, register, loading, error, clearError } = useAuth();

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    try {
      if (mode === 'login') {
        await login(email, password);
        onClose();
        resetForm();
      } else {
        // Validate registration
        if (password !== confirmPassword) {
          setLocalError('Passwords do not match');
          return;
        }
        if (password.length < 8) {
          setLocalError('Password must be at least 8 characters');
          return;
        }
        await register({ email, username, password });
        onClose();
        resetForm();
      }
    } catch {
      // Error is handled by context
    }
  };

  const resetForm = () => {
    setEmail('');
    setUsername('');
    setPassword('');
    setConfirmPassword('');
    setLocalError(null);
  };

  const switchMode = () => {
    setMode(mode === 'login' ? 'register' : 'login');
    resetForm();
    clearError();
  };

  const displayError = localError || error;

  return (
    <div style={overlayStyle}>
      <div style={modalStyle}>
        {/* Header */}
        <div style={headerStyle}>
          <h2 style={{ margin: 0 }}>{mode === 'login' ? 'Login' : 'Create Account'}</h2>
          <button onClick={onClose} style={closeButtonStyle}>&times;</button>
        </div>

        {/* Error Message */}
        {displayError && (
          <div style={errorStyle}>
            {displayError}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} style={formStyle}>
          <div style={fieldStyle}>
            <label style={labelStyle}>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              style={inputStyle}
            />
          </div>

          {mode === 'register' && (
            <div style={fieldStyle}>
              <label style={labelStyle}>Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="johndoe"
                required
                minLength={3}
                pattern="^[a-zA-Z0-9_-]+$"
                title="Letters, numbers, underscores, and hyphens only"
                style={inputStyle}
              />
            </div>
          )}

          <div style={fieldStyle}>
            <label style={labelStyle}>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="********"
              required
              minLength={8}
              style={inputStyle}
            />
          </div>

          {mode === 'register' && (
            <div style={fieldStyle}>
              <label style={labelStyle}>Confirm Password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="********"
                required
                style={inputStyle}
              />
            </div>
          )}

          <button type="submit" disabled={loading} style={submitButtonStyle}>
            {loading ? 'Please wait...' : mode === 'login' ? 'Login' : 'Create Account'}
          </button>
        </form>

        {/* Switch Mode */}
        <div style={switchStyle}>
          {mode === 'login' ? (
            <p>
              Don't have an account?{' '}
              <button onClick={switchMode} style={linkButtonStyle}>
                Sign up
              </button>
            </p>
          ) : (
            <p>
              Already have an account?{' '}
              <button onClick={switchMode} style={linkButtonStyle}>
                Login
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

// Styles - Using CSS variables for theme support
const overlayStyle: React.CSSProperties = {
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
};

const modalStyle: React.CSSProperties = {
  backgroundColor: 'var(--bg-secondary)',
  borderRadius: '0.5rem',
  padding: '1.5rem',
  width: '100%',
  maxWidth: '400px',
  boxShadow: '0 4px 6px var(--shadow-color)',
};

const headerStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginBottom: '1.5rem',
  color: 'var(--text-primary)',
};

const closeButtonStyle: React.CSSProperties = {
  background: 'none',
  border: 'none',
  fontSize: '1.5rem',
  cursor: 'pointer',
  color: 'var(--text-muted)',
};

const errorStyle: React.CSSProperties = {
  backgroundColor: 'var(--error-bg)',
  border: '1px solid var(--error-border)',
  color: 'var(--error-text)',
  padding: '0.75rem',
  borderRadius: '0.375rem',
  marginBottom: '1rem',
  fontSize: '0.875rem',
};

const formStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '1rem',
};

const fieldStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '0.25rem',
};

const labelStyle: React.CSSProperties = {
  fontSize: '0.875rem',
  fontWeight: '500',
  color: 'var(--text-secondary)',
};

const inputStyle: React.CSSProperties = {
  padding: '0.75rem',
  border: '1px solid var(--input-border)',
  borderRadius: '0.375rem',
  fontSize: '1rem',
  backgroundColor: 'var(--input-bg)',
  color: 'var(--text-primary)',
};

const submitButtonStyle: React.CSSProperties = {
  padding: '0.75rem',
  backgroundColor: 'var(--accent-primary)',
  color: 'white',
  border: 'none',
  borderRadius: '0.375rem',
  fontSize: '1rem',
  fontWeight: '500',
  cursor: 'pointer',
  marginTop: '0.5rem',
};

const switchStyle: React.CSSProperties = {
  textAlign: 'center',
  marginTop: '1rem',
  color: 'var(--text-muted)',
  fontSize: '0.875rem',
};

const linkButtonStyle: React.CSSProperties = {
  background: 'none',
  border: 'none',
  color: 'var(--accent-primary)',
  cursor: 'pointer',
  textDecoration: 'underline',
  fontSize: '0.875rem',
};
