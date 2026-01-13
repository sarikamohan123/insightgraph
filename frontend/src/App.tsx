/**
 * Main Application Component
 * ===========================
 *
 * InsightGraph - Knowledge Graph Visualization
 */

import { useState } from 'react';
import { GraphVisualization } from './components/GraphVisualization';
import { GraphForm } from './components/GraphForm';
import { GraphList } from './components/GraphList';
import { ApiKeySettings } from './components/ApiKeySettings';
import { createGraph } from './services/api';
import type { Graph, CreateGraphRequest } from './types';
import './App.css';

function App() {
  const [selectedGraph, setSelectedGraph] = useState<Graph | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleCreateGraph = async (request: CreateGraphRequest) => {
    try {
      setLoading(true);
      const graph = await createGraph(request);
      setSelectedGraph(graph);
      setRefreshTrigger(prev => prev + 1); // Trigger list refresh
    } catch (error: any) {
      if (error.response?.status === 401) {
        throw new Error('Authentication required. Please set your API key above.');
      }
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const handleSelectGraph = (graph: Graph) => {
    setSelectedGraph(graph);
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <h1>InsightGraph</h1>
          <p>Transform text into interactive knowledge graphs</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="main">
        <div className="container">
          {/* API Key Settings */}
          <ApiKeySettings />

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
                    color: '#6b7280',
                    fontSize: '0.875rem',
                  }}>
                    {selectedGraph.description}
                  </p>
                )}
                <GraphVisualization
                  graph={selectedGraph}
                  width={600}
                  height={600}
                />
                {selectedGraph && (
                  <div style={{ marginTop: '1rem', fontSize: '0.875rem', color: '#6b7280' }}>
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
    </div>
  );
}

export default App;
