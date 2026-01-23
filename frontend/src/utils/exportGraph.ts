/**
 * Graph Export Utilities
 * ======================
 *
 * Functions to export graphs in various formats (JSON, PNG, SVG)
 */

import type { Graph } from '../types';

/**
 * Download a file with the given content
 */
const downloadFile = (content: string | Blob, filename: string, mimeType: string) => {
  const blob = content instanceof Blob ? content : new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

/**
 * Generate a safe filename from graph title
 */
const getSafeFilename = (graph: Graph, extension: string): string => {
  const title = graph.title || 'untitled-graph';
  const safeTitle = title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
    .substring(0, 50);
  return `${safeTitle}-${graph.id.substring(0, 8)}.${extension}`;
};

/**
 * Export graph data as JSON
 */
export const exportAsJSON = (graph: Graph): void => {
  const exportData = {
    title: graph.title,
    description: graph.description,
    source_text: graph.source_text,
    nodes: graph.nodes.map(node => ({
      id: node.node_id,
      label: node.label,
      type: node.type,
      confidence: node.confidence,
    })),
    edges: graph.edges.map(edge => ({
      source: edge.source_node_id,
      target: edge.target_node_id,
      relation: edge.relation,
    })),
    metadata: {
      exported_at: new Date().toISOString(),
      total_nodes: graph.nodes.length,
      total_edges: graph.edges.length,
      created_at: graph.created_at,
    },
  };

  const jsonString = JSON.stringify(exportData, null, 2);
  downloadFile(jsonString, getSafeFilename(graph, 'json'), 'application/json');
};

/**
 * Export graph visualization as PNG
 */
export const exportAsPNG = (canvasElement: HTMLCanvasElement | null, graph: Graph): void => {
  if (!canvasElement) {
    console.error('Canvas element not found');
    return;
  }

  // Create a new canvas with white background
  const exportCanvas = document.createElement('canvas');
  exportCanvas.width = canvasElement.width;
  exportCanvas.height = canvasElement.height;
  const ctx = exportCanvas.getContext('2d');

  if (!ctx) {
    console.error('Could not get canvas context');
    return;
  }

  // Fill with white background
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, exportCanvas.width, exportCanvas.height);

  // Draw the original canvas content
  ctx.drawImage(canvasElement, 0, 0);

  // Add title watermark
  ctx.fillStyle = '#6b7280';
  ctx.font = '14px sans-serif';
  ctx.fillText(graph.title || 'Untitled Graph', 10, 20);
  ctx.font = '12px sans-serif';
  ctx.fillText(`Nodes: ${graph.nodes.length} | Edges: ${graph.edges.length}`, 10, 38);

  // Convert to blob and download
  exportCanvas.toBlob((blob) => {
    if (blob) {
      downloadFile(blob, getSafeFilename(graph, 'png'), 'image/png');
    }
  }, 'image/png', 1.0);
};

/**
 * Export graph visualization as SVG
 */
export const exportAsSVG = (graph: Graph, width: number, height: number): void => {
  // Node colors matching the visualization
  const nodeColors: Record<string, string> = {
    Tech: '#3b82f6',
    Concept: '#10b981',
    Person: '#f59e0b',
    default: '#6b7280',
  };

  // Simple force-directed layout calculation
  const nodes = graph.nodes.map((node, i) => {
    const angle = (2 * Math.PI * i) / graph.nodes.length;
    const radius = Math.min(width, height) * 0.35;
    return {
      ...node,
      x: width / 2 + radius * Math.cos(angle),
      y: height / 2 + radius * Math.sin(angle),
    };
  });

  // Create node ID to position map
  const nodePositions = new Map(nodes.map(n => [n.id, { x: n.x, y: n.y }]));

  // Generate SVG content
  let svgContent = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  <rect width="100%" height="100%" fill="white"/>
  <style>
    .node-label { font-family: sans-serif; font-size: 12px; fill: #374151; }
    .edge-label { font-family: sans-serif; font-size: 10px; fill: #6b7280; }
    .title { font-family: sans-serif; font-size: 16px; font-weight: bold; fill: #111827; }
    .subtitle { font-family: sans-serif; font-size: 12px; fill: #6b7280; }
  </style>

  <!-- Title -->
  <text x="20" y="30" class="title">${escapeXml(graph.title || 'Untitled Graph')}</text>
  <text x="20" y="50" class="subtitle">Nodes: ${graph.nodes.length} | Edges: ${graph.edges.length}</text>

  <!-- Edges -->
  <g id="edges">
`;

  // Draw edges
  graph.edges.forEach(edge => {
    const sourcePos = nodePositions.get(edge.source_node_id);
    const targetPos = nodePositions.get(edge.target_node_id);
    if (sourcePos && targetPos) {
      const midX = (sourcePos.x + targetPos.x) / 2;
      const midY = (sourcePos.y + targetPos.y) / 2;
      svgContent += `    <line x1="${sourcePos.x}" y1="${sourcePos.y}" x2="${targetPos.x}" y2="${targetPos.y}" stroke="#9ca3af" stroke-width="2" marker-end="url(#arrowhead)"/>
    <text x="${midX}" y="${midY - 5}" class="edge-label" text-anchor="middle">${escapeXml(edge.relation)}</text>
`;
    }
  });

  svgContent += `  </g>

  <!-- Arrow marker -->
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#9ca3af"/>
    </marker>
  </defs>

  <!-- Nodes -->
  <g id="nodes">
`;

  // Draw nodes
  nodes.forEach(node => {
    const color = nodeColors[node.type] || nodeColors.default;
    svgContent += `    <circle cx="${node.x}" cy="${node.y}" r="20" fill="${color}" stroke="white" stroke-width="2"/>
    <text x="${node.x}" y="${node.y + 35}" class="node-label" text-anchor="middle">${escapeXml(node.label)}</text>
`;
  });

  svgContent += `  </g>
</svg>`;

  downloadFile(svgContent, getSafeFilename(graph, 'svg'), 'image/svg+xml');
};

/**
 * Escape XML special characters
 */
const escapeXml = (str: string): string => {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
};
