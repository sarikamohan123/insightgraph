/**
 * Graph Visualization Component
 * ==============================
 *
 * Interactive force-directed graph visualization using react-force-graph-2d
 */

import { useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import type { ForceGraphData, Graph } from '../types';

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
    <div style={{ border: '1px solid #e5e7eb', borderRadius: '8px', overflow: 'hidden' }}>
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
  );
};
