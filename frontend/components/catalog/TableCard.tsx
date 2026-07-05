"use client";

import { TableItem } from "@/lib/store";

export function TableCard({ item }: { item: TableItem }) {
  return (
    <div className="card">
      <span className="tool-badge">table, renderTable</span>
      {item.title && <div style={{ fontWeight: 600, marginBottom: 8 }}>{item.title}</div>}
      <div style={{ overflowX: "auto" }}>
        <table className="data-table">
          <thead>
            <tr>
              {item.columns.map((column) => (
                <th key={column}>{column}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {item.rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {row.map((cell, cellIndex) => (
                  <td key={cellIndex}>{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
