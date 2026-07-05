"use client";

import { ChartItem } from "@/lib/store";

export function ChartCard({ item }: { item: ChartItem }) {
  const max = Math.max(1, ...item.points.map((point) => point.value));
  const barHeight = 22;
  const gap = 10;
  const labelWidth = 90;
  const trackWidth = 240;
  const height = item.points.length * (barHeight + gap) + gap;

  return (
    <div className="card">
      <span className="tool-badge">chart, renderChart</span>
      {item.title && <div style={{ fontWeight: 600, marginBottom: 8 }}>{item.title}</div>}
      <svg width="100%" viewBox={`0 0 ${labelWidth + trackWidth + 60} ${height}`} role="img">
        {item.points.map((point, index) => {
          const y = gap + index * (barHeight + gap);
          const width = Math.round((point.value / max) * trackWidth);
          return (
            <g key={index}>
              <text x={0} y={y + barHeight * 0.7} className="chart-label">
                {point.label}
              </text>
              <rect
                x={labelWidth}
                y={y}
                width={width}
                height={barHeight}
                rx={4}
                className="chart-bar"
              />
              <text x={labelWidth + width + 6} y={y + barHeight * 0.7} className="chart-value">
                {point.value}
                {item.unit}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
