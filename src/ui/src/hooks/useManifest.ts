import { useState, useEffect } from 'react';
import type { FigureArtifactManifest } from '../types/manifest';

export function useManifest() {
  const [manifest, setManifest] = useState<FigureArtifactManifest | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Expect manifest.json to be in the parent directory of the UI (outputs/figures/)
    fetch('../manifest.json')
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load manifest: ${res.statusText}`);
        return res.json();
      })
      .then((data) => {
        setManifest(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return { manifest, loading, error };
}
