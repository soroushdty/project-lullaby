from __future__ import annotations

import pandas as pd


def feature_importance_rows(model_id: str, repeat: int, fold: int, importance: pd.DataFrame) -> list[dict[str, object]]:
    if importance.empty:
        return []
    rows = []
    for _, row in importance.iterrows():
        rows.append(
            {
                "model_id": model_id,
                "repeat": repeat,
                "fold": fold,
                "feature": row["feature"],
                "importance": float(row["importance"]),
                "rank": int(row["rank"]),
                "notes": "",
            }
        )
    return rows


def local_explanation_notes(enabled_models: list[str]) -> list[str]:
    return [f"local explanations unavailable for {model_id}: no lightweight conforming method configured" for model_id in enabled_models]
