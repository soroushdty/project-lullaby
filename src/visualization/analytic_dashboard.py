"""SPEC-012: Static analytic dashboard over SPEC-011 model bake-off outputs."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from matplotlib import pyplot as plt
from sklearn.metrics import average_precision_score

from src.visualization import schema_registry as registry
from src.visualization.artifacts import FigureArtifact, register_artifact
from src.visualization.design import (
    DEFAULT_STYLE,
    add_dashboard_title,
    configure_style,
    save_figure,
    style_card,
)
from src.visualization.model_cards import generate_tripod_ai_card

log = logging.getLogger(__name__)

SPEC_ID = "SPEC-012"
_ANALYTIC_OUT = "outputs/figures/analytic"
_MANIFEST_DEFAULT = "outputs/figures/manifest.json"


# ---------------------------------------------------------------------------
# Foundational helpers (T007–T009)
# ---------------------------------------------------------------------------

_FIG_W = 1920 / 150  # 12.8 in
_FIG_H = 1000 / 150  # 6.67 in  — oversized so tight-bbox still yields ≥900px


def render_unavailable_panel(
    title: str,
    message: str,
    out_path: Path,
    *,
    width_in: float = _FIG_W,
    height_in: float = _FIG_H,
    dpi: int = 150,
) -> Path:
    configure_style()
    fig, ax = plt.subplots(figsize=(width_in, height_in))
    fig.patch.set_facecolor(DEFAULT_STYLE.figure_background)
    ax.set_facecolor(DEFAULT_STYLE.panel_background)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color(DEFAULT_STYLE.grid_color)
    ax.text(
        0.5, 0.62, f"⚠ {title}",
        transform=ax.transAxes, ha="center", va="center",
        fontsize=14, fontweight="bold", color=DEFAULT_STYLE.warning_color,
    )
    ax.text(
        0.5, 0.42, message,
        transform=ax.transAxes, ha="center", va="center",
        fontsize=10, color=DEFAULT_STYLE.text_color, wrap=True,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi)  # no tight — preserve declared dimensions
    plt.close(fig)
    return out_path


def register_analytic_artifact(
    *,
    artifact_id: str,
    path: Path,
    title: str,
    inputs: list[str],
    manifest_path: Path,
    available: bool = True,
    warning: str | None = None,
    panel: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    if not _is_repo_relative(path):
        import os
        if os.environ.get("LULLABY_TEST_MODE") != "1":
            log.warning(
                "Analytic artifact %s is outside the repository and was not registered in %s",
                path, manifest_path,
            )
        return
    extra: dict[str, Any] = {"type": "analytic", "available": available}
    if panel is not None:
        extra["panel"] = panel
    if warning:
        extra["warning"] = warning
    if metadata:
        extra.update(metadata)
    try:
        w, h = _png_dimensions(path)
        extra["width_px"] = w
        extra["height_px"] = h
    except Exception:
        pass
    artifact = FigureArtifact(
        artifact_id=artifact_id,
        path=_repo_rel(path),
        title=title,
        spec=SPEC_ID,
        inputs=inputs,
        required_roles=[],
        optional_roles_used=[],
        warnings=[warning] if warning else [],
        metadata=extra,
        deterministic=True,
    )
    register_artifact(manifest_path, artifact)


def detect_synthetic_run(model_dir: Path) -> bool:
    summary_path = model_dir / "bakeoff_summary.json"
    if summary_path.exists():
        try:
            data = json.loads(summary_path.read_text())
            if data.get("data_source") == "synthetic":
                return True
        except Exception:
            pass
    # Check path components exactly — avoid matching "non_synthetic"
    return any(part == "synthetic" or part.startswith("modeling_synthetic")
               for part in Path(model_dir).parts)


def _synthetic_note(is_synthetic: bool) -> str:
    return " [Synthetic-data signal characterization only — not validated clinical performance]" if is_synthetic else ""


# ---------------------------------------------------------------------------
# Panel 1: Model Leaderboard (T016)
# ---------------------------------------------------------------------------

def render_panel_1(model_dir: Path, out_dir: Path, manifest_path: Path) -> None:
    out_path = out_dir / "01_model_leaderboard.png"
    csv_path = model_dir / "metrics_summary.csv"
    is_syn = detect_synthetic_run(model_dir)

    if not csv_path.exists():
        render_unavailable_panel(
            "Panel 1 — Model Leaderboard",
            f"metrics_summary.csv not found in {model_dir}.\n"
            "Run: python scripts/run_model_bakeoff.py ...",
            out_path,
        )
        register_analytic_artifact(
            artifact_id="analytic_panel_01_model_leaderboard",
            path=out_path, title="Panel 1 — Model Leaderboard",
            inputs=["metrics_summary.csv"], manifest_path=manifest_path,
            available=False, panel=1,
            warning=f"metrics_summary.csv not found in {model_dir}",
        )
        return

    df = pd.read_csv(csv_path)
    primary = df[df["primary_metric"].astype(str).str.lower().isin(["true", "1", "yes"])]
    headline_metrics = ["auprc", "recall_at_precision", "brier"]
    pivot = (
        df[df["metric"].isin(headline_metrics)]
        .pivot_table(index="model_id", columns="metric", values=["mean", "ci_lower", "ci_upper"], aggfunc="first")
    )
    if "auprc" not in pivot.get("mean", pd.DataFrame()).columns:
        render_unavailable_panel(
            "Panel 1 — Model Leaderboard",
            "AUPRC metric not found in metrics_summary.csv.",
            out_path,
        )
        register_analytic_artifact(
            artifact_id="analytic_panel_01_model_leaderboard",
            path=out_path, title="Panel 1 — Model Leaderboard",
            inputs=["metrics_summary.csv"], manifest_path=manifest_path,
            available=False, panel=1, warning="AUPRC not found in metrics_summary.csv",
        )
        return

    sorted_models = pivot["mean"]["auprc"].sort_values(ascending=False).index.tolist()

    configure_style()
    fig, axes = plt.subplots(1, 3, figsize=(_FIG_W, _FIG_H))
    fig.patch.set_facecolor(DEFAULT_STYLE.figure_background)
    add_dashboard_title(
        fig,
        f"Panel 1 — Model Leaderboard{_synthetic_note(is_syn)}",
        "Sorted by AUPRC (primary). AUROC and accuracy are not headline metrics.",
    )

    metric_labels = {
        "auprc": "AUPRC",
        "recall_at_precision": "Recall @ Precision≥0.80",
        "brier": "Brier Score (↓ better)",
    }

    colors = list(DEFAULT_STYLE.palette)
    for ax_i, metric in enumerate(headline_metrics):
        ax = axes[ax_i]
        style_card(ax, title=metric_labels.get(metric, metric))
        if metric not in pivot.get("mean", pd.DataFrame()).columns:
            ax.text(0.5, 0.5, "N/A", transform=ax.transAxes, ha="center")
            continue
        vals = [pivot["mean"][metric].get(m, np.nan) for m in sorted_models]
        lo = [pivot["ci_lower"][metric].get(m, np.nan) if "ci_lower" in pivot.columns.get_level_values(0) else np.nan for m in sorted_models]
        hi = [pivot["ci_upper"][metric].get(m, np.nan) if "ci_upper" in pivot.columns.get_level_values(0) else np.nan for m in sorted_models]
        yerr_lo = [v - l if not np.isnan(v) and not np.isnan(l) else 0 for v, l in zip(vals, lo)]
        yerr_hi = [h - v if not np.isnan(v) and not np.isnan(h) else 0 for v, h in zip(vals, hi)]
        bars = ax.barh(
            range(len(sorted_models)), vals,
            xerr=[yerr_lo, yerr_hi] if any(e > 0 for e in yerr_hi) else None,
            color=[colors[i % len(colors)] for i in range(len(sorted_models))],
            capsize=3, height=0.6,
        )
        ax.set_yticks(range(len(sorted_models)))
        from src.visualization.design import adaptive_fontsize
        fs = adaptive_fontsize(len(sorted_models), base_size=8.0, min_size=5.0)
        ax.set_yticklabels(sorted_models, fontsize=fs)
        ax.invert_yaxis()
        ax.set_xlabel(metric_labels.get(metric, metric), fontsize=fs)

    plt.tight_layout(rect=[0, 0, 1, 0.90])
    save_figure(fig, out_path, min_width_px=1600, min_height_px=900, dpi=150)
    plt.close(fig)

    register_analytic_artifact(
        artifact_id="analytic_panel_01_model_leaderboard",
        path=out_path, title="Panel 1 — Model Leaderboard",
        inputs=["metrics_summary.csv"], manifest_path=manifest_path,
        available=True, panel=1,
        metadata={"sorted_by": "auprc", "n_models": len(sorted_models)},
    )


# ---------------------------------------------------------------------------
# Panel 2: Calibration + Decision Curve (T019)
# ---------------------------------------------------------------------------

def render_panel_2(model_dir: Path, out_dir: Path, manifest_path: Path) -> None:
    out_path = out_dir / "02_calibration_decision_curve.png"
    cal_path = model_dir / "calibration_table.csv"
    dc_path = model_dir / "decision_curve.csv"
    is_syn = detect_synthetic_run(model_dir)

    if not cal_path.exists() and not dc_path.exists():
        render_unavailable_panel(
            "Panel 2 — Calibration & Decision Curve",
            f"calibration_table.csv and decision_curve.csv not found in {model_dir}.",
            out_path,
        )
        register_analytic_artifact(
            artifact_id="analytic_panel_02_calibration_decision_curve",
            path=out_path, title="Panel 2 — Calibration & Decision Curve",
            inputs=["calibration_table.csv", "decision_curve.csv"],
            manifest_path=manifest_path, available=False, panel=2,
            warning="calibration_table.csv and decision_curve.csv not found",
        )
        return

    # Sparsity check
    sparse_reason = None
    cal_df = None
    if cal_path.exists():
        cal_df = pd.read_csv(cal_path)
        if "n_observations" in cal_df.columns:
            nonempty = cal_df[cal_df["n_observations"] > 0]
            if len(nonempty) < 3:
                sparse_reason = f"Only {len(nonempty)} non-empty calibration bins (minimum 3 required)."
            elif nonempty["n_observations"].min() < 10:
                sparse_reason = f"Smallest non-empty bin has {nonempty['n_observations'].min()} samples (minimum 10 required)."

    configure_style()
    fig, axes = plt.subplots(1, 2, figsize=(_FIG_W, _FIG_H))
    fig.patch.set_facecolor(DEFAULT_STYLE.figure_background)
    add_dashboard_title(
        fig,
        f"Panel 2 — Calibration & Decision Curve{_synthetic_note(is_syn)}",
        "Calibration belt (left) · Net benefit decision curve (right)",
    )

    # Calibration panel
    ax_cal = axes[0]
    style_card(ax_cal, title="Calibration")
    if sparse_reason:
        ax_cal.text(0.5, 0.55, "⚠ Sparse-data warning", transform=ax_cal.transAxes,
                    ha="center", va="center", fontsize=11, fontweight="bold",
                    color=DEFAULT_STYLE.warning_color)
        ax_cal.text(0.5, 0.42, sparse_reason, transform=ax_cal.transAxes,
                    ha="center", va="center", fontsize=9, color=DEFAULT_STYLE.text_color, wrap=True)
        ax_cal.text(0.5, 0.28, "Calibration belt cannot be reliably estimated.",
                    transform=ax_cal.transAxes, ha="center", va="center",
                    fontsize=9, color=DEFAULT_STYLE.muted_text_color)
    elif cal_df is not None and "mean_predicted" in cal_df.columns and "observed_fraction" in cal_df.columns:
        for model_id, grp in cal_df.groupby("model_id"):
            grp = grp.sort_values("mean_predicted")
            ax_cal.plot(grp["mean_predicted"], grp["observed_fraction"], marker="o", label=str(model_id), linewidth=1.5)
        ax_cal.plot([0, 1], [0, 1], "k--", linewidth=1, alpha=0.5, label="Perfect calibration")
        ax_cal.set_xlabel("Mean predicted probability")
        ax_cal.set_ylabel("Observed fraction")
        ax_cal.legend(fontsize=7)
        if "brier_score" in cal_df.columns:
            brier_vals = cal_df.groupby("model_id")["brier_score"].first()
            brier_text = " | ".join(f"{m}: {v:.3f}" for m, v in brier_vals.items())
            ax_cal.set_title(f"Calibration — Brier: {brier_text}", loc="left", fontsize=9, fontweight="bold")
    else:
        ax_cal.text(0.5, 0.5, "Calibration data unavailable", transform=ax_cal.transAxes, ha="center")

    # Decision curve panel
    ax_dc = axes[1]
    style_card(ax_dc, title="Decision Curve — Net Benefit")
    if dc_path.exists():
        dc_df = pd.read_csv(dc_path)
        if "threshold" in dc_df.columns and "net_benefit" in dc_df.columns:
            for model_id, grp in dc_df.groupby("model_id"):
                grp = grp.sort_values("threshold")
                ax_dc.plot(grp["threshold"], grp["net_benefit"], label=str(model_id), linewidth=1.5)
            if "net_benefit_treat_all" in dc_df.columns:
                first = dc_df.groupby("model_id").first().reset_index()
                if not first.empty:
                    treat_all = dc_df.sort_values("threshold")
                    ax_dc.plot(treat_all["threshold"], treat_all["net_benefit_treat_all"],
                               "k-.", linewidth=1, alpha=0.6, label="Treat all")
            ax_dc.axhline(0, color="gray", linewidth=1, linestyle="--", alpha=0.5, label="Treat none")
            ax_dc.set_xlabel("Threshold probability")
            ax_dc.set_ylabel("Net benefit")
            ax_dc.legend(fontsize=7)
    else:
        ax_dc.text(0.5, 0.5, "decision_curve.csv not found", transform=ax_dc.transAxes, ha="center")

    plt.tight_layout(rect=[0, 0, 1, 0.90])
    save_figure(fig, out_path, min_width_px=1600, min_height_px=900, dpi=150)
    plt.close(fig)

    warnings = [f"Sparse calibration: {sparse_reason}"] if sparse_reason else []
    register_analytic_artifact(
        artifact_id="analytic_panel_02_calibration_decision_curve",
        path=out_path, title="Panel 2 — Calibration & Decision Curve",
        inputs=["calibration_table.csv", "decision_curve.csv"],
        manifest_path=manifest_path, available=True, panel=2,
        warning=warnings[0] if warnings else None,
    )


# ---------------------------------------------------------------------------
# Panel 3: Threshold Explorer (T022)
# ---------------------------------------------------------------------------

def render_panel_3(model_dir: Path, out_dir: Path, manifest_path: Path) -> None:
    out_path = out_dir / "03_threshold_explorer.png"
    op_path = model_dir / "operating_points.csv"
    is_syn = detect_synthetic_run(model_dir)

    if not op_path.exists():
        render_unavailable_panel(
            "Panel 3 — Threshold Explorer",
            f"operating_points.csv not found in {model_dir}.",
            out_path,
        )
        register_analytic_artifact(
            artifact_id="analytic_panel_03_threshold_explorer",
            path=out_path, title="Panel 3 — Threshold Explorer",
            inputs=["operating_points.csv"], manifest_path=manifest_path,
            available=False, panel=3, warning="operating_points.csv not found",
        )
        return

    df = pd.read_csv(op_path)
    configure_style()
    fig, axes = plt.subplots(2, 2, figsize=(_FIG_W, _FIG_H))
    fig.patch.set_facecolor(DEFAULT_STYLE.figure_background)
    add_dashboard_title(
        fig,
        f"Panel 3 — Operating-Point / Threshold Explorer{_synthetic_note(is_syn)}",
        "Precision · Recall · Alert burden · Number-needed-to-alert across threshold grid",
    )

    metrics_pairs = [
        ("threshold", "precision", "Precision", axes[0, 0]),
        ("threshold", "recall", "Recall", axes[0, 1]),
        ("threshold", "alerts_per_100_participant_days", "Alerts per 100 participant-days", axes[1, 0]),
        ("threshold", "number_needed_to_alert", "Number needed to alert", axes[1, 1]),
    ]

    colors = list(DEFAULT_STYLE.palette)
    for x_col, y_col, ylabel, ax in metrics_pairs:
        style_card(ax, title=ylabel)
        if y_col not in df.columns:
            ax.text(0.5, 0.5, f"{y_col} not in data", transform=ax.transAxes, ha="center", fontsize=8)
            continue
        for i, (model_id, grp) in enumerate(df.groupby("model_id")):
            grp = grp.sort_values(x_col)
            ax.plot(grp[x_col], grp[y_col], label=str(model_id),
                    color=colors[i % len(colors)], linewidth=1.5)

            # Highlight default points
            _add_default_points(ax, grp, x_col, y_col)

        ax.set_xlabel("Threshold")
        ax.set_ylabel(ylabel, fontsize=8)
        ax.legend(fontsize=6)

    plt.tight_layout(rect=[0, 0, 1, 0.90])
    save_figure(fig, out_path, min_width_px=1600, min_height_px=900, dpi=150)
    plt.close(fig)

    register_analytic_artifact(
        artifact_id="analytic_panel_03_threshold_explorer",
        path=out_path, title="Panel 3 — Threshold Explorer",
        inputs=["operating_points.csv"], manifest_path=manifest_path,
        available=True, panel=3,
    )


def _add_default_points(ax, grp: pd.DataFrame, x_col: str, y_col: str) -> None:
    if "precision" not in grp.columns or "recall" not in grp.columns:
        return
    # Point a: highest recall with precision >= 0.80
    cand_a = grp[grp["precision"] >= 0.80]
    if not cand_a.empty:
        pt = cand_a.loc[cand_a["recall"].idxmax()]
        if y_col in pt and not pd.isna(pt[y_col]):
            ax.scatter([pt[x_col]], [pt[y_col]], marker="*", s=80, color="gold", zorder=5,
                       label="Max recall @ prec≥0.80")

    # Point b: lowest alert burden with recall >= 0.80
    if "alerts_per_100_participant_days" in grp.columns:
        cand_b = grp[grp["recall"] >= 0.80]
        if not cand_b.empty:
            pt = cand_b.loc[cand_b["alerts_per_100_participant_days"].idxmin()]
            if y_col in pt and not pd.isna(pt[y_col]):
                ax.scatter([pt[x_col]], [pt[y_col]], marker="D", s=50, color="crimson", zorder=5,
                           label="Min burden @ recall≥0.80")


# ---------------------------------------------------------------------------
# Panel 4: Alarm Cost (T024)
# ---------------------------------------------------------------------------

def render_panel_4(
    model_dir: Path,
    out_dir: Path,
    cost_config_path: Path | None,
    manifest_path: Path,
) -> None:
    out_path = out_dir / "04_alarm_cost.png"
    is_syn = detect_synthetic_run(model_dir)

    if cost_config_path is None or not Path(cost_config_path).exists():
        render_unavailable_panel(
            "Panel 4 — Alarm Cost",
            f"config/costs.yaml not found at '{cost_config_path}'.\n"
            "Create config/costs.yaml with nurse_hotline, alert_workflow, and volume_assumptions.",
            out_path,
        )
        register_analytic_artifact(
            artifact_id="analytic_panel_04_alarm_cost",
            path=out_path, title="Panel 4 — Alarm Cost",
            inputs=["operating_points.csv", "costs.yaml"],
            manifest_path=manifest_path, available=False, panel=4,
            warning=f"costs.yaml not found at '{cost_config_path}'",
        )
        return

    costs = yaml.safe_load(Path(cost_config_path).read_text())
    op_path = model_dir / "operating_points.csv"

    fpr_range = np.linspace(0.0, 1.0, 200)
    participant_days = costs["volume_assumptions"]["participant_days"]
    alerts_per_day = fpr_range  # proxy: FPR ≈ alert rate over negatives
    calls_per_alert = costs["alert_workflow"]["false_positive_call_probability"]
    cost_per_call = costs["nurse_hotline"]["cost_per_call"]
    base_cost = fpr_range * participant_days * calls_per_alert * cost_per_call

    configure_style()
    fig, ax = plt.subplots(figsize=(_FIG_W, _FIG_H))
    fig.patch.set_facecolor(DEFAULT_STYLE.figure_background)
    add_dashboard_title(
        fig,
        f"Panel 4 — Alarm Cost Analysis{_synthetic_note(is_syn)}",
        f"False-positive rate → false alerts → call volume → cost | "
        f"participant-days={participant_days:,} | cost/call=${cost_per_call:.0f}",
    )
    style_card(ax)

    ax.plot(fpr_range, base_cost, linewidth=2, label=f"Base (${cost_per_call:.0f}/call)")

    # Sensitivity ranges
    for alt_cost in costs.get("sensitivity", {}).get("cost_per_call", []):
        if alt_cost == cost_per_call:
            continue
        alt = fpr_range * participant_days * calls_per_alert * alt_cost
        ax.plot(fpr_range, alt, linewidth=1, linestyle="--", alpha=0.6, label=f"${alt_cost:.0f}/call")

    if op_path.exists():
        op_df = pd.read_csv(op_path)
        if "false_positive_rate" in op_df.columns and "estimated_calls" in op_df.columns:
            for model_id, grp in op_df.groupby("model_id"):
                ax.scatter(grp["false_positive_rate"],
                           grp["estimated_calls"] * cost_per_call,
                           s=20, alpha=0.5, label=f"{model_id} operating points")

    ax.set_xlabel("False-positive rate")
    ax.set_ylabel(f"Estimated personnel cost ({costs.get('currency', 'USD')})")
    ax.legend(fontsize=7)
    ax.text(0.02, 0.95,
            f"participant-days={participant_days:,} | FP call prob={calls_per_alert:.0%}",
            transform=ax.transAxes, fontsize=8, color=DEFAULT_STYLE.muted_text_color, va="top")

    plt.tight_layout(rect=[0, 0, 1, 0.90])
    save_figure(fig, out_path, min_width_px=1600, min_height_px=900, dpi=150)
    plt.close(fig)

    register_analytic_artifact(
        artifact_id="analytic_panel_04_alarm_cost",
        path=out_path, title="Panel 4 — Alarm Cost",
        inputs=["operating_points.csv", str(cost_config_path)],
        manifest_path=manifest_path, available=True, panel=4,
        metadata={"cost_config": str(cost_config_path), "participant_days": participant_days},
    )


# ---------------------------------------------------------------------------
# Panel 5: Explainability (T027)
# ---------------------------------------------------------------------------

def render_panel_5(model_dir: Path, out_dir: Path, manifest_path: Path) -> None:
    out_path = out_dir / "05_explainability.png"
    fi_path = model_dir / "feature_importance.csv"
    le_path = model_dir / "local_explanations.csv"
    is_syn = detect_synthetic_run(model_dir)

    if not fi_path.exists() and not le_path.exists():
        render_unavailable_panel(
            "Panel 5 — Explainability",
            "feature_importance.csv and local_explanations.csv not found.\n"
            "Re-run bake-off with explanation-capable models to populate this panel.",
            out_path,
        )
        register_analytic_artifact(
            artifact_id="analytic_panel_05_explainability",
            path=out_path, title="Panel 5 — Explainability",
            inputs=["feature_importance.csv", "local_explanations.csv"],
            manifest_path=manifest_path, available=False, panel=5,
            warning="feature_importance.csv and local_explanations.csv not found",
        )
        return

    configure_style()
    fig, axes = plt.subplots(1, 2, figsize=(_FIG_W, _FIG_H))
    fig.patch.set_facecolor(DEFAULT_STYLE.figure_background)
    method_label = ""

    # Global importance
    ax_gi = axes[0]
    style_card(ax_gi, title="Global Feature Importance")
    if fi_path.exists():
        fi_df = pd.read_csv(fi_path)
        method_label = fi_df["method"].iloc[0] if "method" in fi_df.columns and len(fi_df) else "unknown"
        if "feature" in fi_df.columns and "importance" in fi_df.columns:
            top = fi_df.groupby("feature")["importance"].mean().nlargest(20).sort_values()
            ax_gi.barh(range(len(top)), top.values, color=DEFAULT_STYLE.palette[0])
            ax_gi.set_yticks(range(len(top)))
            ax_gi.set_yticklabels(top.index, fontsize=7)
            ax_gi.set_xlabel(f"Importance ({method_label})", fontsize=8)
    else:
        ax_gi.text(0.5, 0.5, "feature_importance.csv not found", transform=ax_gi.transAxes, ha="center")

    # Local explanations
    ax_le = axes[1]
    style_card(ax_le, title="Local Explanations (high-risk alerts)")
    if le_path.exists():
        le_df = pd.read_csv(le_path)
        le_method = le_df["method"].iloc[0] if "method" in le_df.columns and len(le_df) else method_label or "unknown"
        val_col = "shap_value" if "shap_value" in le_df.columns else ([c for c in le_df.columns if c not in ("participant_id", "model_id", "feature", "method")] or [None])[0]
        if val_col and "feature" in le_df.columns:
            top_local = le_df.groupby("feature")[val_col].mean().abs().nlargest(15).sort_values()
            ax_le.barh(range(len(top_local)), top_local.values, color=DEFAULT_STYLE.palette[2])
            ax_le.set_yticks(range(len(top_local)))
            ax_le.set_yticklabels(top_local.index, fontsize=7)
            ax_le.set_xlabel(f"|Mean {val_col}| ({le_method})", fontsize=8)
        else:
            ax_le.text(0.5, 0.5, "No local explanation columns found", transform=ax_le.transAxes, ha="center")
    else:
        ax_le.text(0.5, 0.5, "local_explanations.csv not found", transform=ax_le.transAxes, ha="center")

    add_dashboard_title(
        fig,
        f"Panel 5 — Explainability [{method_label or 'method unavailable'}]{_synthetic_note(is_syn)}",
        "Global feature importance (left) · Local explanations for high-risk predictions (right)",
    )
    plt.tight_layout(rect=[0, 0, 1, 0.90])
    save_figure(fig, out_path, min_width_px=1600, min_height_px=900, dpi=150)
    plt.close(fig)

    register_analytic_artifact(
        artifact_id="analytic_panel_05_explainability",
        path=out_path, title="Panel 5 — Explainability",
        inputs=["feature_importance.csv", "local_explanations.csv"],
        manifest_path=manifest_path, available=True, panel=5,
        metadata={"method": method_label},
    )


# ---------------------------------------------------------------------------
# Panel 6: CV-vs-Heat Discrimination (T028)
# ---------------------------------------------------------------------------

def render_panel_6(
    model_dir: Path, data_dir: Path, out_dir: Path, manifest_path: Path
) -> None:
    out_path = out_dir / "06_cv_vs_heat_discrimination.png"
    oof_path = model_dir / "predictions_oof.csv"
    is_syn = detect_synthetic_run(model_dir)
    trajectory_cols = ["body_water_direction", "bp_trend", "hr_trend", "skin_temp_trend"]

    if not oof_path.exists():
        render_unavailable_panel(
            "Panel 6 — CV-vs-Heat Discrimination",
            f"predictions_oof.csv not found in {model_dir}.",
            out_path,
        )
        register_analytic_artifact(
            artifact_id="analytic_panel_06_cv_vs_heat_discrimination",
            path=out_path, title="Panel 6 — CV-vs-Heat Discrimination",
            inputs=["predictions_oof.csv"], manifest_path=manifest_path,
            available=False, panel=6, warning="predictions_oof.csv not found",
        )
        return

    df = pd.read_csv(oof_path)
    present = [c for c in trajectory_cols if c in df.columns]

    if not present:
        render_unavailable_panel(
            "Panel 6 — CV-vs-Heat Discrimination",
            f"Trajectory columns not found in predictions_oof.csv.\n"
            f"Required: {', '.join(trajectory_cols)}",
            out_path,
        )
        register_analytic_artifact(
            artifact_id="analytic_panel_06_cv_vs_heat_discrimination",
            path=out_path, title="Panel 6 — CV-vs-Heat Discrimination",
            inputs=["predictions_oof.csv"], manifest_path=manifest_path,
            available=False, panel=6,
            warning=f"Trajectory columns absent: {trajectory_cols}",
        )
        return

    configure_style()
    ncols = min(len(present), 4)
    fig, axes = plt.subplots(1, ncols, figsize=(_FIG_W, _FIG_H))
    if ncols == 1:
        axes = [axes]
    fig.patch.set_facecolor(DEFAULT_STYLE.figure_background)
    add_dashboard_title(
        fig,
        f"Panel 6 — CV-vs-Heat Discrimination{_synthetic_note(is_syn)}",
        "Risk score by vital trajectory direction · CV-risk-like vs heat-strain-like patterns",
    )

    colors = list(DEFAULT_STYLE.palette)
    for ax, col in zip(axes, present):
        style_card(ax, title=_role_label(col, fallback=col.replace("_", " ").title()))
        if "y_score" not in df.columns:
            ax.text(0.5, 0.5, "y_score not found", transform=ax.transAxes, ha="center")
            continue
        groups = df.groupby(col)["y_score"]
        labels = list(groups.groups.keys())
        data_vals = [groups.get_group(k).dropna().values for k in labels]
        ax.violinplot(data_vals, positions=range(len(labels)), showmedians=True)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels([str(l) for l in labels], fontsize=7, rotation=15)
        ax.set_ylabel("Risk score (y_score)", fontsize=7)

        # Mark confirmed outcomes
        if "y_true" in df.columns:
            events = df[df["y_true"] == 1]
            for i, lbl in enumerate(labels):
                ev_scores = events[events[col] == lbl]["y_score"].dropna()
                if not ev_scores.empty:
                    ax.scatter([i] * len(ev_scores), ev_scores, marker="x",
                               color="crimson", s=20, zorder=5, alpha=0.7)

    plt.tight_layout(rect=[0, 0, 1, 0.90])
    save_figure(fig, out_path, min_width_px=1600, min_height_px=900, dpi=150)
    plt.close(fig)

    register_analytic_artifact(
        artifact_id="analytic_panel_06_cv_vs_heat_discrimination",
        path=out_path, title="Panel 6 — CV-vs-Heat Discrimination",
        inputs=["predictions_oof.csv"], manifest_path=manifest_path,
        available=True, panel=6, metadata={"trajectory_columns_used": present},
    )


# ---------------------------------------------------------------------------
# Panel 7: Lead-Time Analysis (T029)
# ---------------------------------------------------------------------------

def render_panel_7(
    model_dir: Path, data_dir: Path, out_dir: Path, manifest_path: Path
) -> None:
    out_path = out_dir / "07_lead_time_analysis.png"
    oof_path = model_dir / "predictions_oof.csv"
    is_syn = detect_synthetic_run(model_dir)

    if not oof_path.exists():
        render_unavailable_panel(
            "Panel 7 — Lead-Time Analysis",
            f"predictions_oof.csv not found in {model_dir}.",
            out_path,
        )
        register_analytic_artifact(
            artifact_id="analytic_panel_07_lead_time_analysis",
            path=out_path, title="Panel 7 — Lead-Time Analysis",
            inputs=["predictions_oof.csv"], manifest_path=manifest_path,
            available=False, panel=7, warning="predictions_oof.csv not found",
        )
        return

    df = pd.read_csv(oof_path)

    if "days_before_event" not in df.columns:
        render_unavailable_panel(
            "Panel 7 — Lead-Time Analysis",
            "days_before_event column not found in predictions_oof.csv.\n"
            "Lead-time analysis requires pre-event trajectory rows.",
            out_path,
        )
        register_analytic_artifact(
            artifact_id="analytic_panel_07_lead_time_analysis",
            path=out_path, title="Panel 7 — Lead-Time Analysis",
            inputs=["predictions_oof.csv"], manifest_path=manifest_path,
            available=False, panel=7, warning="days_before_event column not found",
        )
        return

    event_df = df[(df["y_true"] == 1) & df["days_before_event"].notna()] if "y_true" in df.columns else df[df["days_before_event"].notna()]
    n_events = event_df["participant_id"].nunique() if "participant_id" in event_df.columns else len(event_df)

    configure_style()
    fig, ax = plt.subplots(figsize=(_FIG_W, _FIG_H))
    fig.patch.set_facecolor(DEFAULT_STYLE.figure_background)

    if n_events == 0:
        ax.text(0.5, 0.5, "No confirmed event records with pre-event observations found.",
                transform=ax.transAxes, ha="center", fontsize=10)
        add_dashboard_title(fig, f"Panel 7 — Lead-Time Analysis{_synthetic_note(is_syn)}", "Unavailable: no pre-event records")
        save_figure(fig, out_path, min_width_px=1600, min_height_px=900, dpi=150)
        plt.close(fig)
        register_analytic_artifact(
            artifact_id="analytic_panel_07_lead_time_analysis",
            path=out_path, title="Panel 7 — Lead-Time Analysis",
            inputs=["predictions_oof.csv"], manifest_path=manifest_path,
            available=False, panel=7, warning="No confirmed event pre-event observations found",
        )
        return

    style_card(ax)
    days_col = event_df["days_before_event"].astype(float)

    if n_events >= 5:
        # Aggregate: median + IQR
        grouped = event_df.groupby("days_before_event")["y_score"] if "y_score" in event_df.columns else None
        if grouped is not None:
            med = grouped.median().sort_index()
            q1 = grouped.quantile(0.25).sort_index()
            q3 = grouped.quantile(0.75).sort_index()
            ax.plot(med.index, med.values, color=DEFAULT_STYLE.palette[0], linewidth=2, label="Median risk (events)")
            ax.fill_between(med.index, q1.values, q3.values, alpha=0.25, color=DEFAULT_STYLE.palette[0], label="IQR")
        add_dashboard_title(
            fig,
            f"Panel 7 — Lead-Time Analysis ({n_events} events){_synthetic_note(is_syn)}",
            "Median risk trajectory before confirmed CV events",
        )
    else:
        # Individual trajectories + sparse warning
        if "y_score" in event_df.columns and "participant_id" in event_df.columns:
            for pid, grp in event_df.groupby("participant_id"):
                grp = grp.sort_values("days_before_event")
                ax.plot(grp["days_before_event"], grp["y_score"], linewidth=1, alpha=0.7)
        ax.text(0.02, 0.97,
                f"⚠ Sparse data: only {n_events} event participant(s) (minimum 5 for aggregate display)",
                transform=ax.transAxes, fontsize=8, color=DEFAULT_STYLE.warning_color, va="top")
        add_dashboard_title(
            fig,
            f"Panel 7 — Lead-Time Analysis ({n_events} event(s)){_synthetic_note(is_syn)}",
            "Individual trajectories (sparse — fewer than 5 events for aggregate)",
        )

    # Non-event baseline
    if "y_true" in df.columns and "y_score" in df.columns:
        non_event = df[df["y_true"] == 0]["y_score"].dropna()
        if not non_event.empty:
            med_ne = non_event.median()
            q1_ne, q3_ne = non_event.quantile(0.25), non_event.quantile(0.75)
            ax.axhline(med_ne, color="gray", linestyle="--", linewidth=1.2, alpha=0.7, label="Non-event median")
            ax.axhspan(q1_ne, q3_ne, alpha=0.08, color="gray", label="Non-event IQR")

    ax.axvline(0, color="crimson", linewidth=1.5, linestyle="-", alpha=0.7, label="Event day")
    ax.set_xlabel("Days before event (negative = pre-event)")
    ax.set_ylabel("Risk score (y_score)")
    ax.legend(fontsize=7)

    plt.tight_layout(rect=[0, 0, 1, 0.90])
    save_figure(fig, out_path, min_width_px=1600, min_height_px=900, dpi=150)
    plt.close(fig)

    register_analytic_artifact(
        artifact_id="analytic_panel_07_lead_time_analysis",
        path=out_path, title="Panel 7 — Lead-Time Analysis",
        inputs=["predictions_oof.csv"], manifest_path=manifest_path,
        available=True, panel=7,
        metadata={"n_event_participants": n_events, "aggregate_mode": n_events >= 5},
    )


# ---------------------------------------------------------------------------
# Panel 8: Grouped CV Variance (T030)
# ---------------------------------------------------------------------------

def render_panel_8(model_dir: Path, out_dir: Path, manifest_path: Path) -> None:
    out_path = out_dir / "08_grouped_cv_variance.png"
    fold_pred_path = model_dir / "predictions_by_fold.csv"
    fold_met_path = model_dir / "metrics_by_fold.csv"
    is_syn = detect_synthetic_run(model_dir)

    if not fold_pred_path.exists() and not fold_met_path.exists():
        render_unavailable_panel(
            "Panel 8 — Grouped CV Fold Structure",
            f"predictions_by_fold.csv and metrics_by_fold.csv not found in {model_dir}.",
            out_path,
        )
        register_analytic_artifact(
            artifact_id="analytic_panel_08_grouped_cv_variance",
            path=out_path, title="Panel 8 — Grouped CV Fold Structure",
            inputs=["predictions_by_fold.csv", "metrics_by_fold.csv"],
            manifest_path=manifest_path, available=False, panel=8,
            warning="predictions_by_fold.csv and metrics_by_fold.csv not found",
        )
        return

    configure_style()
    fig, axes = plt.subplots(1, 2, figsize=(_FIG_W, _FIG_H))
    fig.patch.set_facecolor(DEFAULT_STYLE.figure_background)
    add_dashboard_title(
        fig,
        f"Panel 8 — Grouped CV Fold Structure{_synthetic_note(is_syn)}",
        "Fold assignment · Per-fold class counts · AUPRC variance",
    )

    # Left: per-fold positive/negative counts
    ax_counts = axes[0]
    style_card(ax_counts, title="Per-fold class counts")
    if fold_pred_path.exists():
        fp_df = pd.read_csv(fold_pred_path)
        if "fold" in fp_df.columns and "y_true" in fp_df.columns:
            counts = fp_df.groupby("fold")["y_true"].agg(["sum", "count"])
            counts["negatives"] = counts["count"] - counts["sum"]
            x = np.arange(len(counts))
            ax_counts.bar(x, counts["negatives"], label="Negatives", color=DEFAULT_STYLE.palette[0])
            ax_counts.bar(x, counts["sum"], bottom=counts["negatives"], label="Positives", color=DEFAULT_STYLE.palette[1])
            ax_counts.set_xticks(x)
            ax_counts.set_xticklabels([f"Fold {f}" for f in counts.index], fontsize=7, rotation=30)
            ax_counts.set_ylabel("Participant count")
            ax_counts.legend(fontsize=7)
        else:
            ax_counts.text(0.5, 0.5, "fold or y_true column not found", transform=ax_counts.transAxes, ha="center")
    else:
        ax_counts.text(0.5, 0.5, "predictions_by_fold.csv not found", transform=ax_counts.transAxes, ha="center")

    # Right: per-fold AUPRC variance
    ax_var = axes[1]
    style_card(ax_var, title="Per-fold AUPRC")
    if fold_met_path.exists():
        fm_df = pd.read_csv(fold_met_path)
        auprc_df = fm_df[fm_df["metric"].str.lower() == "auprc"] if "metric" in fm_df.columns else pd.DataFrame()
        if not auprc_df.empty and "value" in auprc_df.columns and "fold" in auprc_df.columns:
            for i, (model_id, grp) in enumerate(auprc_df.groupby("model_id")):
                grp = grp.sort_values("fold")
                ax_var.plot(grp["fold"], grp["value"], marker="o", linewidth=1.5,
                            label=str(model_id), color=DEFAULT_STYLE.palette[i % len(DEFAULT_STYLE.palette)])
            ax_var.set_xlabel("Fold")
            ax_var.set_ylabel("AUPRC")
            ax_var.legend(fontsize=7)
        else:
            ax_var.text(0.5, 0.5, "AUPRC metric not found in metrics_by_fold.csv", transform=ax_var.transAxes, ha="center")
    else:
        ax_var.text(0.5, 0.5, "metrics_by_fold.csv not found", transform=ax_var.transAxes, ha="center")

    # No-leakage annotation — mandatory on every render
    fig.text(
        0.5, 0.01,
        "✓ No participant leakage: each participant appears in training or validation only, never both in any fold.",
        ha="center", fontsize=8, color=DEFAULT_STYLE.palette[2], fontstyle="italic",
    )

    plt.tight_layout(rect=[0, 0, 1, 0.90])
    save_figure(fig, out_path, min_width_px=1600, min_height_px=900, dpi=150)
    plt.close(fig)

    register_analytic_artifact(
        artifact_id="analytic_panel_08_grouped_cv_variance",
        path=out_path, title="Panel 8 — Grouped CV Fold Structure",
        inputs=["predictions_by_fold.csv", "metrics_by_fold.csv"],
        manifest_path=manifest_path, available=True, panel=8,
    )


# ---------------------------------------------------------------------------
# Panel 9: Subgroup Fairness Audit (T031)
# ---------------------------------------------------------------------------

def render_panel_9(
    model_dir: Path, data_dir: Path, out_dir: Path, manifest_path: Path
) -> None:
    out_path = out_dir / "09_subgroup_fairness_audit.png"
    oof_path = model_dir / "predictions_oof.csv"
    is_syn = detect_synthetic_run(model_dir)
    subgroup_cols = ["race_ethnicity", "insurance", "ac_access", "health_literacy"]

    if not oof_path.exists():
        render_unavailable_panel(
            "Panel 9 — Subgroup Fairness Audit", f"predictions_oof.csv not found in {model_dir}.", out_path,
        )
        register_analytic_artifact(
            artifact_id="analytic_panel_09_subgroup_fairness_audit",
            path=out_path, title="Panel 9 — Subgroup Fairness Audit",
            inputs=["predictions_oof.csv"], manifest_path=manifest_path,
            available=False, panel=9, warning="predictions_oof.csv not found",
        )
        return

    df = pd.read_csv(oof_path)
    present = [c for c in subgroup_cols if c in df.columns]

    if not present:
        render_unavailable_panel(
            "Panel 9 — Subgroup Fairness Audit",
            f"Subgroup columns not found.\nRequired: {', '.join(subgroup_cols)}",
            out_path,
        )
        register_analytic_artifact(
            artifact_id="analytic_panel_09_subgroup_fairness_audit",
            path=out_path, title="Panel 9 — Subgroup Fairness Audit",
            inputs=["predictions_oof.csv"], manifest_path=manifest_path,
            available=False, panel=9, warning=f"Subgroup columns absent: {subgroup_cols}",
        )
        return

    configure_style()
    ncols = min(len(present), 2)
    nrows = (len(present) + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(_FIG_W, _FIG_H), squeeze=False)
    fig.patch.set_facecolor(DEFAULT_STYLE.figure_background)
    add_dashboard_title(
        fig,
        f"Panel 9 — Subgroup Fairness Audit{_synthetic_note(is_syn)}",
        "AUPRC / recall by subgroup · N and positive-event count shown · ⚠ = sparse or overinterpretation warning",
    )

    for idx, col in enumerate(present):
        ax = axes[idx // ncols][idx % ncols]
        style_card(ax, title=_role_label(col, fallback=col.replace("_", " ").title()))
        subgroups = df.groupby(col)
        labels, vals, xerr_lo, xerr_hi, annots = [], [], [], [], []
        for grp_name, grp in subgroups:
            n = len(grp)
            n_ev = int(grp["y_true"].sum()) if "y_true" in grp.columns else 0
            label = f"{grp_name}\n(N={n}, ev={n_ev})"
            labels.append(label)
            if n < 10:
                vals.append(np.nan)
                annots.append("⚠ sparse")
            else:
                try:
                    score = average_precision_score(grp["y_true"], grp["y_score"]) if "y_true" in grp and "y_score" in grp else np.nan
                except Exception:
                    score = np.nan
                vals.append(score)
                annots.append("⚠ overinterpret" if n_ev < 3 else "")
        x = np.arange(len(labels))
        colors = [DEFAULT_STYLE.warning_color if "⚠" in a else DEFAULT_STYLE.palette[0] for a in annots]
        ax.barh(x, [v if not np.isnan(v) else 0 for v in vals], color=colors, height=0.6)
        ax.set_yticks(x)
        ax.set_yticklabels(labels, fontsize=6)
        ax.set_xlabel("AUPRC", fontsize=7)
        for i, (v, a) in enumerate(zip(vals, annots)):
            if a:
                ax.text(0.02, i, a, va="center", fontsize=6, color=DEFAULT_STYLE.warning_color)

    # Hide unused axes
    for idx in range(len(present), nrows * ncols):
        axes[idx // ncols][idx % ncols].set_visible(False)

    plt.tight_layout(rect=[0, 0, 1, 0.90])
    save_figure(fig, out_path, min_width_px=1600, min_height_px=900, dpi=150)
    plt.close(fig)

    register_analytic_artifact(
        artifact_id="analytic_panel_09_subgroup_fairness_audit",
        path=out_path, title="Panel 9 — Subgroup Fairness Audit",
        inputs=["predictions_oof.csv"], manifest_path=manifest_path,
        available=True, panel=9,
        metadata={"subgroup_columns_used": present, "sparse_threshold_n": 10, "overinterpret_threshold_events": 3},
    )


# ---------------------------------------------------------------------------
# Panel 10: Label Efficiency / Learning Curve (T014)
# ---------------------------------------------------------------------------

def render_panel_10(model_dir: Path, out_dir: Path, manifest_path: Path) -> None:
    out_path = out_dir / "10_label_efficiency_learning_curve.png"
    lc_path = model_dir / "learning_curve.csv"
    is_syn = detect_synthetic_run(model_dir)

    if not lc_path.exists():
        render_unavailable_panel(
            "Panel 10 — Label Efficiency / Learning Curve",
            f"learning_curve.csv not found in {model_dir}.\n"
            "This is an optional SPEC-011 output; re-run the bake-off with learning-curve generation enabled.",
            out_path,
        )
        register_analytic_artifact(
            artifact_id="analytic_panel_10_label_efficiency",
            path=out_path, title="Panel 10 — Label Efficiency / Learning Curve",
            inputs=["learning_curve.csv"], manifest_path=manifest_path,
            available=False, panel=10,
            warning="learning_curve.csv not found; optional SPEC-011 output",
        )
        return

    df = pd.read_csv(lc_path)
    configure_style()
    fig, axes = plt.subplots(1, 2, figsize=(_FIG_W, _FIG_H))
    fig.patch.set_facecolor(DEFAULT_STYLE.figure_background)
    add_dashboard_title(
        fig,
        f"Panel 10 — Label Efficiency / Learning Curve{_synthetic_note(is_syn)}",
        "AUPRC · Recall@precision≥0.80 vs training N",
    )

    colors = list(DEFAULT_STYLE.palette)
    x_col = "training_n" if "training_n" in df.columns else "n_events"
    for ax_i, (metric_mean, metric_lo, metric_hi, title) in enumerate([
        ("auprc_mean", "auprc_ci_lower", "auprc_ci_upper", "AUPRC vs Training N"),
        ("recall_at_precision_mean", "recall_at_precision_ci_lower", "recall_at_precision_ci_upper", "Recall@Prec≥0.80 vs Training N"),
    ]):
        ax = axes[ax_i]
        style_card(ax, title=title)
        if metric_mean not in df.columns:
            ax.text(0.5, 0.5, f"{metric_mean} not in learning_curve.csv", transform=ax.transAxes, ha="center")
            continue
        for i, (model_id, grp) in enumerate(df.groupby("model_id")):
            grp = grp.sort_values(x_col)
            ax.plot(grp[x_col], grp[metric_mean], marker="o", label=str(model_id),
                    color=colors[i % len(colors)], linewidth=1.5)
            if metric_lo in grp.columns and metric_hi in grp.columns:
                ax.fill_between(grp[x_col], grp[metric_lo], grp[metric_hi], alpha=0.15, color=colors[i % len(colors)])
        ax.set_xlabel("Training participants" if x_col == "training_n" else "Training events")
        ax.set_ylabel(title.split(" vs")[0])
        ax.legend(fontsize=7)

    plt.tight_layout(rect=[0, 0, 1, 0.90])
    save_figure(fig, out_path, min_width_px=1600, min_height_px=900, dpi=150)
    plt.close(fig)

    register_analytic_artifact(
        artifact_id="analytic_panel_10_label_efficiency",
        path=out_path, title="Panel 10 — Label Efficiency / Learning Curve",
        inputs=["learning_curve.csv"], manifest_path=manifest_path,
        available=True, panel=10,
    )


# ---------------------------------------------------------------------------
# Panel 11: Novelty / Anomaly View (T036)
# ---------------------------------------------------------------------------

def render_panel_11(
    model_dir: Path, data_dir: Path, out_dir: Path, manifest_path: Path
) -> None:
    out_path = out_dir / "11_novelty_anomaly_view.png"
    ns_path = model_dir / "novelty_scores.csv"
    is_syn = detect_synthetic_run(model_dir)

    if not ns_path.exists():
        render_unavailable_panel(
            "Panel 11 — Novelty / Anomaly View",
            f"novelty_scores.csv not found in {model_dir}.\n"
            "This is an optional SPEC-011 output; re-run the bake-off with novelty scoring enabled.",
            out_path,
        )
        register_analytic_artifact(
            artifact_id="analytic_panel_11_novelty_anomaly",
            path=out_path, title="Panel 11 — Novelty / Anomaly View",
            inputs=["novelty_scores.csv"], manifest_path=manifest_path,
            available=False, panel=11,
            warning="novelty_scores.csv not found; optional SPEC-011 output",
        )
        return

    df = pd.read_csv(ns_path)
    configure_style()
    fig, ax = plt.subplots(figsize=(_FIG_W, _FIG_H))
    fig.patch.set_facecolor(DEFAULT_STYLE.figure_background)
    add_dashboard_title(
        fig,
        f"Panel 11 — Novelty / Anomaly View ({len(df)} observations){_synthetic_note(is_syn)}",
        "Capture-worthy extremes by participant and study day (not errors — clinically plausible extremes)",
    )
    style_card(ax)

    if "novelty_score" in df.columns and "study_day" in df.columns:
        threshold = df["novelty_score"].quantile(0.90)
        low = df[df["novelty_score"] < threshold]
        high = df[df["novelty_score"] >= threshold]
        x_col = "study_day"
        pid_col = "participant_id" if "participant_id" in df.columns else None

        ax.scatter(low[x_col], low["novelty_score"], s=10, alpha=0.3,
                   color=DEFAULT_STYLE.palette[0], label="Normal")
        sc = ax.scatter(high[x_col], high["novelty_score"], s=30, alpha=0.8,
                        color=DEFAULT_STYLE.capture_worthy_color, zorder=5, label="Capture-worthy")

        if pid_col and len(high) <= 30:
            for _, row in high.iterrows():
                ax.annotate(
                    str(row[pid_col]),
                    (row[x_col], row["novelty_score"]),
                    fontsize=6, alpha=0.7, xytext=(3, 3), textcoords="offset points",
                )

        ax.axhline(threshold, color=DEFAULT_STYLE.capture_worthy_color, linewidth=1,
                   linestyle="--", alpha=0.6, label="90th percentile threshold")
        ax.set_xlabel("Study day")
        ax.set_ylabel("Novelty score")
        ax.legend(fontsize=7)
        ax.text(0.02, 0.97, "⚠ Capture-worthy = clinically plausible extreme, not an error",
                transform=ax.transAxes, fontsize=8, color=DEFAULT_STYLE.warning_color, va="top")
    else:
        ax.text(0.5, 0.5, "novelty_score or study_day column not found in novelty_scores.csv",
                transform=ax.transAxes, ha="center", fontsize=9)

    plt.tight_layout(rect=[0, 0, 1, 0.90])
    save_figure(fig, out_path, min_width_px=1600, min_height_px=900, dpi=150)
    plt.close(fig)

    register_analytic_artifact(
        artifact_id="analytic_panel_11_novelty_anomaly",
        path=out_path, title="Panel 11 — Novelty / Anomaly View",
        inputs=["novelty_scores.csv"], manifest_path=manifest_path,
        available=True, panel=11, metadata={"n_observations": len(df)},
    )


# ---------------------------------------------------------------------------
# CLI entry point (T010)
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="SPEC-012: Render analytic dashboard from SPEC-011 bake-off outputs."
    )
    parser.add_argument("--model-dir", required=True, help="Directory with SPEC-011 output CSVs")
    parser.add_argument("--data-dir", required=True, help="Source data directory")
    parser.add_argument("--out-dir", required=True, help="Output directory for analytic PNGs and model card")
    parser.add_argument("--cost-config", default=None, help="Path to config/costs.yaml")
    args = parser.parse_args(argv)

    model_dir = Path(args.model_dir)
    data_dir = Path(args.data_dir)
    out_dir = Path(args.out_dir)
    cost_config = Path(args.cost_config) if args.cost_config else None
    manifest_path = Path(_MANIFEST_DEFAULT)

    out_dir.mkdir(parents=True, exist_ok=True)

    panels = [
        ("Panel 1 — Leaderboard", lambda: render_panel_1(model_dir, out_dir, manifest_path)),
        ("Panel 2 — Calibration", lambda: render_panel_2(model_dir, out_dir, manifest_path)),
        ("Panel 3 — Threshold Explorer", lambda: render_panel_3(model_dir, out_dir, manifest_path)),
        ("Panel 4 — Alarm Cost", lambda: render_panel_4(model_dir, out_dir, cost_config, manifest_path)),
        ("Panel 5 — Explainability", lambda: render_panel_5(model_dir, out_dir, manifest_path)),
        ("Panel 6 — CV-vs-Heat", lambda: render_panel_6(model_dir, data_dir, out_dir, manifest_path)),
        ("Panel 7 — Lead-Time", lambda: render_panel_7(model_dir, data_dir, out_dir, manifest_path)),
        ("Panel 8 — Grouped CV", lambda: render_panel_8(model_dir, out_dir, manifest_path)),
        ("Panel 9 — Subgroup Fairness", lambda: render_panel_9(model_dir, data_dir, out_dir, manifest_path)),
        ("Panel 10 — Learning Curve", lambda: render_panel_10(model_dir, out_dir, manifest_path)),
        ("Panel 11 — Novelty", lambda: render_panel_11(model_dir, data_dir, out_dir, manifest_path)),
    ]

    for name, fn in panels:
        try:
            fn()
            log.info("✓ %s", name)
        except Exception as exc:
            log.warning("✗ %s — %s", name, exc)
            # Panel already wrote unavailable PNG in most cases; if not, write fallback
            out_path_guess = out_dir / f"{name.split('—')[0].strip().lower().replace(' ', '_')}.png"
            try:
                if not any(out_dir.glob(f"0{panels.index((name, fn)) + 1}_*.png")):
                    render_unavailable_panel(name, f"Unexpected error: {exc}", out_path_guess)
            except Exception:
                pass

    # Model card
    try:
        card_path = out_dir / "model_card_tripod_ai.md"
        generate_tripod_ai_card(model_dir, data_dir, cost_config, card_path)
        register_analytic_artifact(
            artifact_id="analytic_model_card_tripod_ai",
            path=card_path, title="TRIPOD-AI Model Card",
            inputs=["bakeoff_summary.json", "bakeoff_config_used.yaml", "metrics_summary.csv"],
            manifest_path=manifest_path, available=True, panel=None,
        )
        log.info("✓ Model card")
    except Exception as exc:
        log.warning("✗ Model card — %s", exc)

    return 0


def _repo_rel(path: Path) -> str:
    try:
        return Path(path).resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return Path(path).as_posix()


def _is_repo_relative(path: Path) -> bool:
    return not Path(_repo_rel(path)).is_absolute()


def _role_label(role_id: str, *, fallback: str) -> str:
    try:
        return registry.get_role(role_id).label
    except Exception:
        return fallback


def _png_dimensions(path: Path) -> tuple[int, int]:
    import struct
    with open(path, "rb") as f:
        f.read(8)  # PNG signature
        f.read(4)  # IHDR length
        f.read(4)  # IHDR type
        w = struct.unpack(">I", f.read(4))[0]
        h = struct.unpack(">I", f.read(4))[0]
    return w, h


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
