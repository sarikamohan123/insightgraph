/**
 * Skeleton Loading Components
 * ============================
 *
 * Placeholder components that show while content is loading.
 * Provides a smoother, less "jumpy" loading experience.
 */

import React from 'react';

// Base skeleton with pulse animation
const skeletonStyle: React.CSSProperties = {
  backgroundColor: 'var(--bg-tertiary)',
  borderRadius: '0.375rem',
  animation: 'skeleton-pulse 1.5s ease-in-out infinite',
};

// Skeleton for text lines
export const SkeletonText: React.FC<{ width?: string; height?: string }> = ({
  width = '100%',
  height = '1rem',
}) => (
  <div
    style={{
      ...skeletonStyle,
      width,
      height,
    }}
  />
);

// Skeleton for a graph card in the list
export const SkeletonGraphCard: React.FC = () => (
  <div
    style={{
      padding: '1rem',
      border: '1px solid var(--border-color)',
      borderRadius: '0.5rem',
      backgroundColor: 'var(--bg-secondary)',
    }}
  >
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
      <div style={{ flex: 1 }}>
        {/* Title + Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
          <SkeletonText width="60%" height="1.25rem" />
          <SkeletonText width="50px" height="1rem" />
        </div>
        {/* Description lines */}
        <SkeletonText width="100%" height="0.875rem" />
        <div style={{ marginTop: '0.5rem' }}>
          <SkeletonText width="85%" height="0.875rem" />
        </div>
        {/* Meta info */}
        <div style={{ display: 'flex', gap: '1rem', marginTop: '0.75rem' }}>
          <SkeletonText width="60px" height="0.75rem" />
          <SkeletonText width="60px" height="0.75rem" />
          <SkeletonText width="80px" height="0.75rem" />
        </div>
      </div>
      {/* Action buttons placeholder */}
      <div style={{ display: 'flex', gap: '0.5rem', marginLeft: '1rem' }}>
        <SkeletonText width="80px" height="32px" />
        <SkeletonText width="60px" height="32px" />
      </div>
    </div>
  </div>
);

// Skeleton for the entire graph list
export const SkeletonGraphList: React.FC<{ count?: number }> = ({ count = 3 }) => (
  <div style={{ display: 'grid', gap: '1rem' }}>
    {Array.from({ length: count }).map((_, index) => (
      <SkeletonGraphCard key={index} />
    ))}
  </div>
);

// Skeleton for the graph visualization area
export const SkeletonVisualization: React.FC = () => (
  <div
    style={{
      ...skeletonStyle,
      width: '100%',
      height: '400px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}
  >
    <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
      <div
        style={{
          width: '48px',
          height: '48px',
          margin: '0 auto 1rem',
          borderRadius: '50%',
          backgroundColor: 'var(--border-color)',
        }}
      />
      <SkeletonText width="120px" height="1rem" />
    </div>
  </div>
);
