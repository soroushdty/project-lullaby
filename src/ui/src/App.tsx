import React, { useState, useEffect } from 'react';
import { useManifest } from './hooks/useManifest';
import { Sidebar } from './components/Sidebar';
import { ImageViewer } from './components/ImageViewer';

const App: React.FC = () => {
  const { manifest, loading, error } = useManifest();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    if (manifest?.entries.length && !selectedId) {
      setSelectedId(manifest.entries[0].artifact_id);
    }
  }, [manifest]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-900 text-white">
        <div className="flex flex-col items-center">
          <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="mt-4 font-medium text-slate-400">Loading Pipeline Manifest...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-900 text-white p-12">
        <div className="max-w-md bg-slate-800 p-8 rounded-2xl border border-rose-500/50 shadow-2xl">
          <h2 className="text-xl font-bold text-rose-400 mb-4">Connection Error</h2>
          <p className="text-slate-300 leading-relaxed">{error}</p>
          <div className="mt-6 pt-6 border-t border-slate-700">
            <p className="text-xs text-slate-500 font-mono">
              Ensure you are serving this directory with a web server (e.g. python -m http.server) and manifest.json exists in the parent folder.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const selectedArtifact = manifest?.entries.find(e => e.artifact_id === selectedId);

  return (
    <div className="flex min-h-screen bg-white font-sans text-slate-900">
      {manifest && (
        <Sidebar 
          artifacts={manifest.entries} 
          selectedId={selectedId} 
          onSelect={setSelectedId} 
        />
      )}
      {selectedArtifact ? (
        <ImageViewer artifact={selectedArtifact} />
      ) : (
        <div className="flex-1 flex items-center justify-center bg-slate-50">
          <p className="text-slate-400 italic">Select a dashboard from the sidebar to begin review.</p>
        </div>
      )}
    </div>
  );
};

export default App;
