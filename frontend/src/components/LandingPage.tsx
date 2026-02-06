/**
 * Landing Page Component
 * =======================
 *
 * Professional marketing page to showcase InsightGraph
 * before users sign up or enter the app.
 */

import React from 'react';

interface LandingPageProps {
  onGetStarted: () => void;
  onLogin: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onGetStarted, onLogin }) => {
  return (
    <div className="landing-page">
      {/* Navigation */}
      <nav className="landing-nav">
        <div className="landing-nav-content">
          <div className="landing-logo">
            <span className="logo-icon">🧠</span>
            <span className="logo-text">InsightGraph</span>
          </div>
          <div className="landing-nav-links">
            <a href="#features">Features</a>
            <a href="#how-it-works">How it Works</a>
            <a href="#demo">Demo</a>
            <button className="btn-secondary" onClick={onLogin}>Login</button>
            <button className="btn-primary" onClick={onGetStarted}>Get Started</button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <div className="hero-badge">AI-Powered Knowledge Extraction</div>
          <h1 className="hero-title">
            Transform Text into
            <span className="gradient-text"> Interactive Knowledge Graphs</span>
          </h1>
          <p className="hero-subtitle">
            Unlock hidden insights from any text. Our AI extracts entities and relationships,
            creating beautiful visualizations that make complex information easy to understand.
          </p>
          <div className="hero-ctas">
            <button className="btn-primary btn-large" onClick={onGetStarted}>
              Start Creating
              <span className="btn-arrow">→</span>
            </button>
            <a href="#demo" className="btn-secondary btn-large">
              See it in Action
            </a>
          </div>
          <div className="hero-stats">
            <div className="stat">
              <span className="stat-number">AI</span>
              <span className="stat-label">Powered Extraction</span>
            </div>
            <div className="stat-divider" />
            <div className="stat">
              <span className="stat-number">100%</span>
              <span className="stat-label">Easy to Use</span>
            </div>
            <div className="stat-divider" />
            <div className="stat">
              <span className="stat-number">Fast</span>
              <span className="stat-label">Instant Results</span>
            </div>
          </div>
        </div>
        <div className="hero-visual">
          <div className="hero-graph-preview">
            <svg viewBox="0 0 400 300" className="graph-illustration">
              {/* Animated graph illustration */}
              <defs>
                <linearGradient id="nodeGradient1" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#667eea" />
                  <stop offset="100%" stopColor="#764ba2" />
                </linearGradient>
                <linearGradient id="nodeGradient2" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#f093fb" />
                  <stop offset="100%" stopColor="#f5576c" />
                </linearGradient>
                <linearGradient id="nodeGradient3" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#4facfe" />
                  <stop offset="100%" stopColor="#00f2fe" />
                </linearGradient>
              </defs>
              {/* Edges */}
              <line x1="200" y1="80" x2="100" y2="180" className="graph-edge" />
              <line x1="200" y1="80" x2="300" y2="180" className="graph-edge" />
              <line x1="100" y1="180" x2="200" y2="250" className="graph-edge" />
              <line x1="300" y1="180" x2="200" y2="250" className="graph-edge" />
              <line x1="100" y1="180" x2="300" y2="180" className="graph-edge" />
              {/* Nodes */}
              <circle cx="200" cy="80" r="30" fill="url(#nodeGradient1)" className="graph-node node-1" />
              <circle cx="100" cy="180" r="25" fill="url(#nodeGradient2)" className="graph-node node-2" />
              <circle cx="300" cy="180" r="25" fill="url(#nodeGradient3)" className="graph-node node-3" />
              <circle cx="200" cy="250" r="22" fill="url(#nodeGradient1)" className="graph-node node-4" />
              {/* Labels */}
              <text x="200" y="85" textAnchor="middle" className="node-label">AI</text>
              <text x="100" y="185" textAnchor="middle" className="node-label">ML</text>
              <text x="300" y="185" textAnchor="middle" className="node-label">Data</text>
              <text x="200" y="255" textAnchor="middle" className="node-label">Insights</text>
            </svg>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="features-section">
        <div className="section-header">
          <h2>Powerful Features</h2>
          <p>Everything you need to extract and visualize knowledge from text</p>
        </div>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">🤖</div>
            <h3>AI-Powered Extraction</h3>
            <p>
              Powered by Google Gemini, our AI understands context and extracts
              meaningful entities and relationships from any text.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🎨</div>
            <h3>Interactive Visualization</h3>
            <p>
              Beautiful force-directed graphs that you can drag, zoom, and explore.
              Watch your knowledge come to life.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🔍</div>
            <h3>Semantic Search</h3>
            <p>
              Find graphs by meaning, not just keywords. Our AI understands
              what you're looking for.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🌐</div>
            <h3>Public Portfolio</h3>
            <p>
              Share your knowledge graphs with the world. Perfect for showcasing
              research or building your portfolio.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🌙</div>
            <h3>Dark Mode</h3>
            <p>
              Easy on the eyes with automatic dark mode support. Works with
              your system preferences.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">⚡</div>
            <h3>Lightning Fast</h3>
            <p>
              Built with modern tech stack for instant results. No waiting
              around for your insights.
            </p>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="how-it-works-section">
        <div className="section-header">
          <h2>How It Works</h2>
          <p>Three simple steps to unlock insights from any text</p>
        </div>
        <div className="steps-container">
          <div className="step">
            <div className="step-number">1</div>
            <div className="step-content">
              <h3>Paste Your Text</h3>
              <p>
                Enter any text - articles, research papers, meeting notes,
                or documentation. Our AI handles it all.
              </p>
            </div>
          </div>
          <div className="step-connector" />
          <div className="step">
            <div className="step-number">2</div>
            <div className="step-content">
              <h3>AI Extracts Knowledge</h3>
              <p>
                Our AI identifies entities (people, technologies, concepts)
                and discovers how they're connected.
              </p>
            </div>
          </div>
          <div className="step-connector" />
          <div className="step">
            <div className="step-number">3</div>
            <div className="step-content">
              <h3>Explore & Share</h3>
              <p>
                Interact with your knowledge graph, discover insights,
                and share publicly or keep private.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Demo Section */}
      <section id="demo" className="demo-section">
        <div className="section-header">
          <h2>See It In Action</h2>
          <p>Watch how InsightGraph transforms text into knowledge</p>
        </div>
        <div className="demo-container">
          <div className="demo-input">
            <div className="demo-label">Input Text</div>
            <div className="demo-text">
              "Machine learning is revolutionizing healthcare by enabling early disease
              detection. Deep learning, a subset of machine learning, uses neural networks
              to analyze medical images. TensorFlow and PyTorch are popular frameworks
              used by researchers."
            </div>
          </div>
          <div className="demo-arrow">→</div>
          <div className="demo-output">
            <div className="demo-label">Knowledge Graph</div>
            <div className="demo-graph">
              <svg viewBox="0 0 300 200" className="demo-graph-svg">
                <line x1="150" y1="40" x2="60" y2="100" stroke="var(--border-color)" strokeWidth="2" />
                <line x1="150" y1="40" x2="240" y2="100" stroke="var(--border-color)" strokeWidth="2" />
                <line x1="60" y1="100" x2="100" y2="160" stroke="var(--border-color)" strokeWidth="2" />
                <line x1="240" y1="100" x2="200" y2="160" stroke="var(--border-color)" strokeWidth="2" />
                <line x1="60" y1="100" x2="240" y2="100" stroke="var(--border-color)" strokeWidth="2" opacity="0.5" />

                <circle cx="150" cy="40" r="20" fill="#667eea" />
                <circle cx="60" cy="100" r="18" fill="#f093fb" />
                <circle cx="240" cy="100" r="18" fill="#4facfe" />
                <circle cx="100" cy="160" r="15" fill="#f5576c" />
                <circle cx="200" cy="160" r="15" fill="#00f2fe" />

                <text x="150" y="44" textAnchor="middle" fill="white" fontSize="8">ML</text>
                <text x="60" y="104" textAnchor="middle" fill="white" fontSize="7">DL</text>
                <text x="240" y="104" textAnchor="middle" fill="white" fontSize="6">Health</text>
                <text x="100" y="163" textAnchor="middle" fill="white" fontSize="6">TF</text>
                <text x="200" y="163" textAnchor="middle" fill="white" fontSize="6">PyT</text>
              </svg>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="cta-content">
          <h2>Ready to Unlock Your Insights?</h2>
          <p>Join now and start creating beautiful knowledge graphs in seconds.</p>
          <button className="btn-primary btn-large" onClick={onGetStarted}>
            Get Started
            <span className="btn-arrow">→</span>
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="footer-content">
          <div className="footer-brand">
            <span className="logo-icon">🧠</span>
            <span className="logo-text">InsightGraph</span>
          </div>
          <div className="footer-links">
            <a href="https://github.com/sarikamohan123/insightgraph" target="_blank" rel="noopener noreferrer">
              GitHub
            </a>
            <a href="#features">Features</a>
            <a href="#how-it-works">How it Works</a>
          </div>
          <div className="footer-credit">
            Built with React, FastAPI & Gemini AI
          </div>
        </div>
      </footer>
    </div>
  );
};
