export interface FigureArtifact {
  artifact_id: string;
  path: string;
  title: string;
  spec: string;
  inputs: string[];
  required_roles: string[];
  optional_roles_used: string[];
  warnings: string[];
  created_at_utc: string;
  deterministic: boolean;
  metadata: {
    available?: boolean;
    type?: 'analytic' | 'eda';
    panel?: number;
    warning?: string;
    [key: string]: any;
  };
}

export interface FigureArtifactManifest {
  schema_version: string;
  manifest_path: string;
  entries: FigureArtifact[];
  warnings: string[];
}
