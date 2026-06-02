import React from 'react';
import type { FigureArtifact } from '../types/manifest';

interface ImageViewerProps {
  artifact: FigureArtifact;
}

export const ImageViewer: React.FC<ImageViewerProps> = ({ artifact }) => {
  const isAvailable = artifact.metadata.available !== false;
  
  return (
    <div className="flex-1 flex flex-col bg-slate-50 min-h-screen">
      <div className="p-8 max-w-6xl mx-auto w-full space-y-8">
        <header className="flex justify-between items-end border-b border-slate-200 pb-6">
          <div>
            <span className="text-xs font-bold text-indigo-600 uppercase tracking-widest bg-indigo-50 px-2 py-1 rounded">
              {artifact.spec}
            </span>
            <h2 className="text-3xl font-extrabold text-slate-900 mt-3 tracking-tight">
              {artifact.title}
            </h2>
          </div>
          <div className="text-right text-xs text-slate-500 font-medium">
            Generated: {new Date(artifact.created_at_utc).toLocaleDateString()}
          </div>
        </header>

        <main className="space-y-8">
          <div className="bg-white rounded-xl shadow-xl shadow-slate-200/50 border border-slate-200 overflow-hidden ring-1 ring-slate-900/5">
            {isAvailable ? (
              <img 
                src={`../${artifact.path}`} 
                alt={artifact.title}
                className="w-full h-auto block"
              />
            ) : (
              <div className="aspect-[16/9] flex flex-col items-center justify-center p-12 text-center bg-slate-50">
                <div className="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mb-4">
                  <span className="text-2xl text-amber-600 font-bold">!</span>
                </div>
                <h3 className="text-lg font-bold text-slate-900 mb-2">Panel Unavailable</h3>
                <p className="text-slate-600 max-w-md">
                  {artifact.metadata.warning || "This panel was skipped during pipeline execution due to missing or insufficient input data."}
                </p>
                <div className="mt-6 p-4 bg-white border border-slate-200 rounded-lg text-left w-full max-w-lg">
                  <p className="text-xs font-bold text-slate-400 uppercase mb-2">Required Roles:</p>
                  <div className="flex flex-wrap gap-2">
                    {artifact.required_roles.map(role => (
                      <code key={role} className="text-[10px] bg-slate-100 px-2 py-1 rounded text-slate-700">{role}</code>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <h4 className="text-xs font-bold text-slate-400 uppercase mb-4 tracking-wider">Provenance & Integrity</h4>
              <ul className="space-y-3">
                <li className="flex justify-between text-sm">
                  <span className="text-slate-500">Deterministic</span>
                  <span className={`font-mono font-bold ${artifact.deterministic ? 'text-emerald-600' : 'text-amber-600'}`}>
                    {artifact.deterministic ? 'VERIFIED' : 'FALSE'}
                  </span>
                </li>
                <li className="flex justify-between text-sm">
                  <span className="text-slate-500">Source Artifact</span>
                  <code className="text-[11px] bg-slate-50 px-2 py-1 rounded truncate ml-4" title={artifact.artifact_id}>
                    {artifact.artifact_id}
                  </code>
                </li>
              </ul>
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm md:col-span-2">
              <h4 className="text-xs font-bold text-slate-400 uppercase mb-4 tracking-wider">Clinical Metadata</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-slate-500 mb-1">Inputs:</p>
                  <div className="flex flex-wrap gap-1">
                    {artifact.inputs.map(input => (
                      <span key={input} className="text-[11px] bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded font-medium">{input}</span>
                    ))}
                  </div>
                </div>
                {artifact.warnings.length > 0 && (
                  <div>
                    <p className="text-amber-600 font-bold mb-1">Alerts/Warnings:</p>
                    <ul className="list-disc list-inside text-xs text-amber-700 space-y-1">
                      {artifact.warnings.map((w, i) => (
                        <li key={i}>{w}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
};
