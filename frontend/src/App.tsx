/**
 * Main Application Component
 * ===========================
 *
 * InsightGraph - Knowledge Graph Visualization
 */

import { useState, useEffect } from 'react';
import { Analytics } from '@vercel/analytics/react';
import { GraphVisualization } from './components/GraphVisualization';
import { GraphForm } from './components/GraphForm';
import { GraphList } from './components/GraphList';
import { AuthModal } from './components/AuthModal';
import { LandingPage } from './components/LandingPage';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';
import { createGraph } from './services/api';
import type { Graph, CreateGraphRequest } from './types';
import './App.css';
import './components/LandingPage.css';

function AppContent() {
  const [selectedGraph, setSelectedGraph] = useState<Graph | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showLanding, setShowLanding] = useState(() => {
    // Check if user has visited before
    return !localStorage.getItem('insightgraph_visited');
  });

  const { user, isAuthenticated, logout } = useAuth();
  const { isDark, toggleTheme } = useTheme();

  // When user logs in, hide landing page
  useEffect(() => {
    if (isAuthenticated) {
      setShowLanding(false);
      localStorage.setItem('insightgraph_visited', 'true');
    }
  }, [isAuthenticated]);

  const handleEnterApp = () => {
    setShowLanding(false);
    localStorage.setItem('insightgraph_visited', 'true');
  };

  const handleLoginFromLanding = () => {
    setShowAuthModal(true);
  };

  const handleCreateGraph = async (request: CreateGraphRequest) => {
    // Check if user is authenticated
    if (!isAuthenticated) {
      setShowAuthModal(true);
      throw new Error('Please login to create graphs');
    }

    try {
      setLoading(true);
      const graph = await createGraph(request);
      setSelectedGraph(graph);
      setRefreshTrigger(prev => prev + 1);
    } catch (error: any) {
      if (error.response?.status === 401) {
        setShowAuthModal(true);
        throw new Error('Please login to create graphs');
      }
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const handleSelectGraph = (graph: Graph) => {
    setSelectedGraph(graph);
  };

  // Show landing page for first-time visitors
  if (showLanding) {
    return (
      <>
        <LandingPage onGetStarted={handleEnterApp} onLogin={handleLoginFromLanding} />
        <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} />
      </>
    );
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ minWidth: '200px' }}>
            <h1>InsightGraph</h1>
            <p className="hide-mobile">Transform text into interactive knowledge graphs</p>
          </div>
          <div className="header-actions" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="theme-toggle"
              title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {isDark ? '☀️' : '🌙'}
            </button>

            {isAuthenticated ? (
              <>
                {/* Full user info - hidden on mobile */}
                <div className="hide-mobile" style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  padding: '0.5rem 0.75rem',
                  borderRadius: '0.375rem',
                }}>
                  <div style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '50%',
                    backgroundColor: '#3b82f6',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                    fontSize: '0.75rem',
                    fontWeight: '600',
                  }}>
                    {user?.username?.charAt(0).toUpperCase()}
                  </div>
                  <span style={{ color: 'white', fontSize: '0.875rem' }}>
                    {user?.username}
                  </span>
                </div>
                {/* Avatar only - shown on mobile */}
                <div className="show-mobile" style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  backgroundColor: '#3b82f6',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  fontSize: '0.875rem',
                  fontWeight: '600',
                }}>
                  {user?.username?.charAt(0).toUpperCase()}
                </div>
                <button
                  onClick={logout}
                  style={{
                    padding: '0.5rem 0.75rem',
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    color: 'white',
                    border: '1px solid rgba(255, 255, 255, 0.3)',
                    borderRadius: '0.375rem',
                    cursor: 'pointer',
                    fontSize: '0.875rem',
                  }}
                >
                  Logout
                </button>
              </>
            ) : (
              <button
                onClick={() => setShowAuthModal(true)}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: 'white',
                  color: '#3b82f6',
                  border: 'none',
                  borderRadius: '0.375rem',
                  cursor: 'pointer',
                  fontWeight: '500',
                  fontSize: '0.875rem',
                }}
              >
                Login
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main">
        <div className="container">
          {/* Auth Status Banner */}
          {!isAuthenticated && (
            <div className="auth-banner" style={{
              backgroundColor: 'var(--warning-bg)',
              border: '1px solid var(--warning-border)',
              borderRadius: '0.5rem',
              padding: '1rem',
              marginBottom: '1.5rem',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '0.75rem',
            }}>
              <span style={{ color: 'var(--warning-text)', flex: '1', minWidth: '200px' }}>
                Login to create and save your own knowledge graphs
              </span>
              <button
                onClick={() => setShowAuthModal(true)}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: 'var(--accent-primary)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '0.375rem',
                  cursor: 'pointer',
                  fontSize: '0.875rem',
                  whiteSpace: 'nowrap',
                }}
              >
                Login
              </button>
            </div>
          )}

          {/* Two Column Layout */}
          <div className="grid">
            {/* Left Column - Form and List */}
            <div className="column">
              <section className="section">
                <h2>Create New Graph</h2>
                <GraphForm onSubmit={handleCreateGraph} loading={loading} />
              </section>

              <section className="section" style={{ marginTop: '2rem' }}>
                <h2>Saved Graphs</h2>
                <GraphList
                  onSelectGraph={handleSelectGraph}
                  refreshTrigger={refreshTrigger}
                />
              </section>
            </div>

            {/* Right Column - Visualization */}
            <div className="column">
              <section className="section sticky">
                <h2>
                  {selectedGraph
                    ? selectedGraph.title || 'Untitled Graph'
                    : 'Graph Visualization'}
                </h2>
                {selectedGraph && selectedGraph.description && (
                  <p style={{
                    marginTop: '0.5rem',
                    marginBottom: '1rem',
                    color: 'var(--text-muted)',
                    fontSize: '0.875rem',
                  }}>
                    {selectedGraph.description}
                  </p>
                )}
                <GraphVisualization
                  graph={selectedGraph}
                  width={800}
                  height={500}
                />
                {selectedGraph && (
                  <div style={{ marginTop: '1rem', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                    <p><strong>Nodes:</strong> {selectedGraph.nodes.length}</p>
                    <p><strong>Edges:</strong> {selectedGraph.edges.length}</p>
                    <p><strong>Created:</strong> {new Date(selectedGraph.created_at).toLocaleString()}</p>
                  </div>
                )}
              </section>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="footer">
        <p>
          Powered by{' '}
          <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer">
            InsightGraph API
          </a>
        </p>
      </footer>

      {/* Auth Modal */}
      <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} />
    </div>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppContent />
        <Analytics />
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
