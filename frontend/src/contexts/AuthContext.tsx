/**
 * Authentication Context
 * ======================
 *
 * Provides authentication state and methods across the app.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getCurrentUser, login as apiLogin, logout as apiLogout, register as apiRegister, getJwtToken } from '../services/api';
import type { User, RegisterRequest } from '../types';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Check authentication status
  const checkAuth = useCallback(async (isInitialCheck = false) => {
    const token = getJwtToken();
    if (token) {
      try {
        const currentUser = await getCurrentUser();
        setUser(currentUser);
      } catch {
        // Token invalid or expired
        apiLogout();
        setUser(null);
      }
    } else {
      setUser(null);
    }
    if (isInitialCheck) {
      setLoading(false);
    }
  }, []);

  // Check for existing session on mount
  useEffect(() => {
    checkAuth(true);
  }, [checkAuth]);

  // Periodic token validation (every 5 minutes)
  useEffect(() => {
    if (!user) return;

    const intervalId = setInterval(() => {
      checkAuth();
    }, 5 * 60 * 1000); // 5 minutes

    return () => clearInterval(intervalId);
  }, [user, checkAuth]);

  // Re-validate when tab regains focus
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && getJwtToken()) {
        checkAuth();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [checkAuth]);

  const login = useCallback(async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      await apiLogin(email, password);
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Login failed';
      setError(message);
      throw new Error(message);
    } finally {
      setLoading(false);
    }
  }, []);

  const register = useCallback(async (data: RegisterRequest) => {
    setLoading(true);
    setError(null);
    try {
      await apiRegister(data);
      // Auto-login after registration
      await apiLogin(data.email, data.password);
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Registration failed';
      setError(message);
      throw new Error(message);
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    apiLogout();
    setUser(null);
    setError(null);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const value: AuthContextType = {
    user,
    loading,
    error,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
