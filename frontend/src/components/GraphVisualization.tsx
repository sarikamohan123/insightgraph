/**
 * Graph Visualization Component
 * ==============================
 *
 * Interactive force-directed graph visualization using react-force-graph-2d
 * with export capabilities (JSON, PNG, SVG)
 */

import { useRef, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import type { ForceGraphData, Graph } from '../types';
import { exportAsJSON, exportAsPNG, exportAsSVG } from '../utils/exportGraph';

interface GraphVisualizationProps {
  graph: Graph | null;
  width?: number;
  height?: number;
}

// Color mapping for different node types
const NODE_COLORS: Record<string, string> = {
  Tech: '#3b82f6',      // Blue
  Concept: '#10b981',   // Green
  Person: '#f59e0b',    // Orange
  default: '#6b7280',   // Gray
};

export const GraphVisualization: React.FC<GraphVisualizationProps> = ({
  graph,
  width = 800,
  height = 600,
}) => {
  const fgRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Convert backend graph format to force-graph format
  const convertToForceGraph = (g: Graph): ForceGraphData => {
    const nodes = g.nodes.map(node => ({
      id: node.id,
      name: node.label,
      type: node.type,
      confidence: node.confidence,
    }));

    const links = g.edges.map(edge => ({
      source: edge.source_node_id,
      target: edge.target_node_id,
      relation: edge.relation,
    }));

    return { nodes, links };
  };

  // Export handlers
  const handleExportJSON = useCallback(() => {
    if (graph) exportAsJSON(graph);
  }, [graph]);

  const handleExportPNG = useCallback(() => {
    if (graph && containerRef.current) {
      // Find the canvas element inside the container
      const canvas = containerRef.current.querySelector('canvas');
      exportAsPNG(canvas, graph);
    }
  }, [graph]);

  const handleExportSVG = useCallback(() => {
    if (graph) exportAsSVG(graph, width, height);
  }, [graph, width, height]);

  if (!graph) {
    return (
      <div
        style={{
          width,
          height,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#f9fafb',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
        }}
      >
        <p style={{ color: '#6b7280' }}>No graph to display</p>
      </div>
    );
  }

  const graphData = convertToForceGraph(graph);

  return (
    <div>
      <div ref={containerRef} style={{ border: '1px solid #e5e7eb', borderRadius: '8px', overflow: 'hidden' }}>
        <ForceGraph2D
          ref={fgRef}
          graphData={graphData}
          width={width}
          height={height}
          nodeLabel={(node: any) => `${node.name} (${node.type}) - ${(node.confidence * 100).toFixed(0)}%`}
          nodeColor={(node: any) => NODE_COLORS[node.type] || NODE_COLORS.default}
          nodeRelSize={6}
          linkLabel={(link: any) => link.relation}
          linkColor={() => '#9ca3af'}
          linkDirectionalArrowLength={4}
          linkDirectionalArrowRelPos={0.8}
          linkWidth={2}
          enableNodeDrag={true}
          enablePanInteraction={true}
          cooldownTicks={100}
          onEngineStop={() => fgRef.current?.zoomToFit(400)}
        />
      </div>

      {/* Export Buttons */}
      <div style={{
        display: 'flex',
        gap: '0.5rem',
        marginTop: '1rem',
        flexWrap: 'wrap',
      }}>
        <button
          onClick={handleExportJSON}
          style={exportButtonStyle}
          title="Download graph data as JSON"
        >
          Export JSON
        </button>
        <button
          onClick={handleExportPNG}
          style={exportButtonStyle}
          title="Download visualization as PNG image"
        >
          Export PNG
        </button>
        <button
          onClick={handleExportSVG}
          style={exportButtonStyle}
          title="Download visualization as SVG vector"
        >
          Export SVG
        </button>
      </div>
    </div>
  );
};

// Export button style
const exportButtonStyle: React.CSSProperties = {
  padding: '0.5rem 1rem',
  backgroundColor: '#f3f4f6',
  color: '#374151',
  border: '1px solid #d1d5db',
  borderRadius: '0.375rem',
  fontSize: '0.875rem',
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  gap: '0.5rem',
};
