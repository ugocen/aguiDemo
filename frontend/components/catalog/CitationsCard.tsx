"use client";

import { CitationsItem } from "@/lib/store";

export function CitationsCard({ item }: { item: CitationsItem }) {
  return (
    <div className="card">
      <span className="tool-badge">citations, renderCitations</span>
      {item.title && <div style={{ fontWeight: 600, marginBottom: 8 }}>{item.title}</div>}
      <ol className="citations-list">
        {item.sources.map((source, index) => (
          <li key={index}>
            {source.url ? (
              <a href={source.url} target="_blank" rel="noreferrer" className="citation-title">
                {source.title}
              </a>
            ) : (
              <span className="citation-title">{source.title}</span>
            )}
            {source.snippet && <div className="citation-snippet">{source.snippet}</div>}
          </li>
        ))}
      </ol>
    </div>
  );
}
