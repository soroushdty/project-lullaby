from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

try:  # pragma: no cover - exercised when the optional runtime dependency is installed.
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.neural_network import MLPClassifier
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    SKLEARN_AVAILABLE = True
except Exception:  # pragma: no cover - current Python 3.14 test venv may lack wheels.
    GradientBoostingClassifier = None
    RandomForestClassifier = None
    SimpleImputer = None
    LogisticRegression = None
    MLPClassifier = None
    Pipeline = None
    StandardScaler = None
    SKLEARN_AVAILABLE = False


class ModelError(ValueError):
    """Raised when a model cannot be configured or fit."""


@dataclass
class ModelSpec:
    model_id: str
    family: str
    requires_scaling: bool
    supports_feature_importance: bool = True
    supports_class_weight: bool = True
    notes: str = ""


class WeightedLogisticEstimator:
    def __init__(self, *, random_state: int, learning_rate: float = 0.08, max_iter: int = 450, l2: float = 0.01) -> None:
        self.random_state = int(random_state)
        self.learning_rate = float(learning_rate)
        self.max_iter = int(max_iter)
        self.l2 = float(l2)
        self.coef_: np.ndarray | None = None
        self.intercept_: float = 0.0

    def fit(self, x: np.ndarray, y: np.ndarray, sample_weight: np.ndarray | None = None) -> "WeightedLogisticEstimator":
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        if len(np.unique(y)) < 2:
            raise ModelError("Training fold contains one class")
        rng = np.random.default_rng(self.random_state)
        self.coef_ = rng.normal(0, 0.01, size=x.shape[1])
        self.intercept_ = 0.0
        weights = np.ones_like(y) if sample_weight is None else np.asarray(sample_weight, dtype=float)
        weights = weights / max(weights.mean(), 1e-12)
        lr = self.learning_rate
        for _ in range(self.max_iter):
            logits = np.clip(x @ self.coef_ + self.intercept_, -30, 30)
            probs = 1.0 / (1.0 + np.exp(-logits))
            error = (probs - y) * weights
            grad_w = (x.T @ error) / len(y) + self.l2 * self.coef_
            grad_b = float(error.mean())
            self.coef_ -= lr * grad_w
            self.intercept_ -= lr * grad_b
        return self

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        if self.coef_ is None:
            raise ModelError("Estimator is not fitted")
        logits = np.clip(np.asarray(x, dtype=float) @ self.coef_ + self.intercept_, -30, 30)
        probs = 1.0 / (1.0 + np.exp(-logits))
        return np.column_stack([1.0 - probs, probs])


class FoldPipeline:
    def __init__(self, spec: ModelSpec, *, random_state: int, class_weight: str | None = "balanced") -> None:
        self.spec = spec
        self.random_state = int(random_state)
        self.class_weight = class_weight
        self.feature_columns: list[str] = []
        self.medians_: np.ndarray | None = None
        self.means_: np.ndarray | None = None
        self.scales_: np.ndarray | None = None
        self.estimator: WeightedLogisticEstimator | None = None
        self.notes: list[str] = []

    def _weights(self, y: np.ndarray) -> np.ndarray:
        if self.class_weight != "balanced" or not self.spec.supports_class_weight:
            if self.class_weight == "balanced" and not self.spec.supports_class_weight:
                self.notes.append(f"{self.spec.model_id} does not support class_weight; using unweighted fit")
            return np.ones_like(y, dtype=float)
        positives = max(int(np.sum(y == 1)), 1)
        negatives = max(int(np.sum(y == 0)), 1)
        n = len(y)
        return np.where(y == 1, n / (2 * positives), n / (2 * negatives)).astype(float)

    def _prepare_fit(self, x: pd.DataFrame) -> np.ndarray:
        self.feature_columns = list(x.columns)
        values = x.to_numpy(dtype=float)
        self.medians_ = np.nanmedian(values, axis=0)
        self.medians_ = np.where(np.isfinite(self.medians_), self.medians_, 0.0)
        values = np.where(np.isnan(values), self.medians_, values)
        if self.spec.requires_scaling:
            self.means_ = values.mean(axis=0)
            self.scales_ = values.std(axis=0)
            self.scales_ = np.where(self.scales_ > 1e-12, self.scales_, 1.0)
            values = (values - self.means_) / self.scales_
        else:
            self.means_ = np.zeros(values.shape[1])
            self.scales_ = np.ones(values.shape[1])
        return values

    def _prepare_predict(self, x: pd.DataFrame) -> np.ndarray:
        if self.medians_ is None or self.means_ is None or self.scales_ is None:
            raise ModelError("Pipeline is not fitted")
        aligned = x.reindex(columns=self.feature_columns)
        values = aligned.to_numpy(dtype=float)
        values = np.where(np.isnan(values), self.medians_, values)
        if self.spec.requires_scaling:
            values = (values - self.means_) / self.scales_
        return values

    def fit(self, x: pd.DataFrame, y: np.ndarray) -> "FoldPipeline":
        y = np.asarray(y).astype(int)
        x_prepared = self._prepare_fit(x)
        params = {
            "baseline_meows_logistic": {"learning_rate": 0.08, "max_iter": 350, "l2": 0.04},
            "random_forest": {"learning_rate": 0.06, "max_iter": 420, "l2": 0.02},
            "gradient_boosting": {"learning_rate": 0.10, "max_iter": 460, "l2": 0.015},
            "mlp": {"learning_rate": 0.05, "max_iter": 500, "l2": 0.01},
        }.get(self.spec.model_id, {"learning_rate": 0.08, "max_iter": 400, "l2": 0.02})
        self.estimator = WeightedLogisticEstimator(random_state=self.random_state, **params)
        self.estimator.fit(x_prepared, y, sample_weight=self._weights(y))
        return self

    def predict_scores(self, x: pd.DataFrame) -> np.ndarray:
        if self.estimator is None:
            raise ModelError("Pipeline is not fitted")
        scores = self.estimator.predict_proba(self._prepare_predict(x))[:, 1]
        return np.clip(scores, 0.0, 1.0)

    def feature_importance(self) -> pd.DataFrame:
        if self.estimator is None or self.estimator.coef_ is None or not self.spec.supports_feature_importance:
            return pd.DataFrame()
        values = np.abs(self.estimator.coef_)
        order = np.argsort(-values)
        return pd.DataFrame(
            {
                "feature": [self.feature_columns[i] for i in order],
                "importance": values[order],
                "rank": np.arange(1, len(order) + 1),
            }
        )


class SklearnFoldPipeline(FoldPipeline):
    def __init__(self, spec: ModelSpec, *, random_state: int, class_weight: str | None = "balanced") -> None:
        super().__init__(spec, random_state=random_state, class_weight=class_weight)
        self.pipeline_model: Any | None = None

    def _make_estimator(self) -> Any:
        balanced = self.class_weight if self.class_weight == "balanced" else None
        if self.spec.model_id == "baseline_meows_logistic":
            return LogisticRegression(class_weight=balanced, max_iter=1000, random_state=self.random_state, solver="liblinear")
        if self.spec.model_id == "random_forest":
            return RandomForestClassifier(
                n_estimators=80,
                max_depth=5,
                class_weight=balanced,
                random_state=self.random_state,
                n_jobs=1,
            )
        if self.spec.model_id == "gradient_boosting":
            return GradientBoostingClassifier(random_state=self.random_state)
        if self.spec.model_id == "mlp":
            return MLPClassifier(
                hidden_layer_sizes=(16,),
                activation="relu",
                solver="lbfgs",
                alpha=0.001,
                max_iter=500,
                random_state=self.random_state,
            )
        raise ModelError(f"Unsupported model_id {self.spec.model_id}")

    def fit(self, x: pd.DataFrame, y: np.ndarray) -> "SklearnFoldPipeline":
        y = np.asarray(y).astype(int)
        if len(np.unique(y)) < 2:
            raise ModelError("Training fold contains one class")
        self.feature_columns = list(x.columns)
        values = x.to_numpy(dtype=float)
        self.medians_ = np.nanmedian(values, axis=0)
        self.medians_ = np.where(np.isfinite(self.medians_), self.medians_, 0.0)
        self.means_ = np.zeros(values.shape[1])
        self.scales_ = np.ones(values.shape[1])
        steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
        if self.spec.requires_scaling:
            steps.append(("scaler", StandardScaler()))
        steps.append(("estimator", self._make_estimator()))
        self.pipeline_model = Pipeline(steps)
        self._weights(y)
        self.pipeline_model.fit(x.copy(), y)
        return self

    def predict_scores(self, x: pd.DataFrame) -> np.ndarray:
        if self.pipeline_model is None:
            raise ModelError("Pipeline is not fitted")
        aligned = x.reindex(columns=self.feature_columns)
        scores = self.pipeline_model.predict_proba(aligned)[:, 1]
        return np.clip(scores, 0.0, 1.0)

    def feature_importance(self) -> pd.DataFrame:
        if self.pipeline_model is None or not self.spec.supports_feature_importance:
            return pd.DataFrame()
        estimator = self.pipeline_model.named_steps["estimator"]
        if hasattr(estimator, "feature_importances_"):
            values = np.asarray(estimator.feature_importances_, dtype=float)
        elif hasattr(estimator, "coef_"):
            values = np.abs(np.asarray(estimator.coef_, dtype=float)).reshape(-1)
        else:
            return pd.DataFrame()
        order = np.argsort(-values)
        return pd.DataFrame(
            {
                "feature": [self.feature_columns[i] for i in order],
                "importance": values[order],
                "rank": np.arange(1, len(order) + 1),
            }
        )


def enabled_model_specs(config: dict[str, Any]) -> list[ModelSpec]:
    models = config.get("models", {})
    specs = [
        ModelSpec("baseline_meows_logistic", "baseline", True, True, True),
        ModelSpec("random_forest", "classic_ml", False, True, True),
        ModelSpec("gradient_boosting", "classic_ml", False, True, False, "class_weight unsupported by fallback gradient boosting"),
        ModelSpec("mlp", "neural", True, True, False, "class_weight unsupported by fallback MLP"),
    ]
    enabled = [spec for spec in specs if models.get(spec.model_id, {}).get("enabled", True)]
    if len(enabled) < 3:
        raise ModelError("At least three default model families must be enabled")
    return enabled


def make_pipeline(spec: ModelSpec, *, seed: int, class_weight: str | None) -> FoldPipeline:
    if SKLEARN_AVAILABLE:
        return SklearnFoldPipeline(spec, random_state=seed, class_weight=class_weight)
    return FoldPipeline(spec, random_state=seed, class_weight=class_weight)
