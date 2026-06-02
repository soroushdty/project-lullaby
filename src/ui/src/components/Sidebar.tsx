import React from 'react';
import type { FigureArtifact } from '../types/manifest';

interface SidebarProps {
  artifacts: FigureArtifact[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ artifacts, selectedId, onSelect }) => {
  const groups = artifacts.reduce((acc, art) => {
    const type = art.artifact_id.startsWith('analytic') ? 'Analytic' : 'EDA';
    if (!acc[type]) acc[type] = [];
    acc[type].push(art);
    return acc;
  }, {} as Record<string, FigureArtifact[]>);

  return (
    <div className="w-64 bg-slate-900 text-slate-100 flex flex-col h-screen sticky top-0 overflow-y-auto border-r border-slate-700">
      <div className="p-6 border-b border-slate-800">
        <h1 className="text-xl font-bold tracking-tight text-white">Project Lullaby</h1>
        <p className="text-xs text-slate-400 mt-1 uppercase tracking-widest font-semibold">Dashboard Viewer</p>
      </div>
      <nav className="flex-1 px-2 py-4 space-y-8">
        {Object.entries(groups).map(([type, items]) => (
          <div key={type}>
            <h3 className="px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
              {type} Dashboards
            </h3>
            <div className="space-y-1">
              {items.map((art) => (
                <button
                  key={art.artifact_id}
                  onClick={() => onSelect(art.artifact_id)}
                  className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${
                    selectedId === art.artifact_id
                      ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/20 font-medium'
                      : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  {art.title.replace('Panel ', 'P').replace('EDA ', '')}
                </button>
              ))}
            </div>
          </div>
        ))}
      </nav>
      <div className="p-4 bg-slate-950 border-t border-slate-800 text-[10px] text-slate-500 font-mono">
        v0.1.0 | SPEC-014
      </div>
    </div>
  );
};
