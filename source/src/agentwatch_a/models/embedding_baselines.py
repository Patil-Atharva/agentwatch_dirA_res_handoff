"""Pooled embedding anomaly detectors (B2: Isolation Forest / One-Class SVM / Mahalanobis).

Adheres to Section 8.1 and Section 8.3 of AGENTWATCH_DIRECTION_A_SPEC.md.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import TYPE_CHECKING, Literal

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import OneClassSVM

from agentwatch_a.models.interface import BaseMonitorScorer, PreExecutionInput

if TYPE_CHECKING:
    from agentwatch_a.schemas import TrajectoryTrace

DetectorAlgorithm = Literal["isolation_forest", "ocsvm"]


def _format_pre_execution_text(event_input: PreExecutionInput) -> str:
    """Extract deterministic text prefix up to decision point t (Section 6.1)."""
    parts: list[str] = [f"Goal: {event_input.goal}"]
    if event_input.prior_observations:
        # Include observations up to t-1
        recent_obs = " ".join(event_input.prior_observations[-3:])  # recent context window
        parts.append(f"Recent Observations: {recent_obs}")

    args_str = json.dumps(event_input.proposed_args, sort_keys=True)
    parts.append(f"Proposed: {event_input.proposed_tool}({args_str})")
    return " | ".join(parts)


class PooledEmbeddingAnomalyBaseline(BaseMonitorScorer):
    """Baseline B2: Fits an unsupervised anomaly detector over pooled benign prefix representations."""

    def __init__(
        self,
        algorithm: DetectorAlgorithm = "isolation_forest",
        max_features: int = 128,
        random_state: int = 17,
    ):
        self.algorithm = algorithm
        self.max_features = max_features
        self.random_state = random_state

        self.vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            ngram_range=(1, 2),
                    )

        if self.algorithm == "isolation_forest":
            self.detector = IsolationForest(
                n_estimators=100,
                random_state=self.random_state,
                contamination="auto",
            )
        elif self.algorithm == "ocsvm":
            self.detector = OneClassSVM(kernel="rbf", gamma="scale")
        else:
            raise ValueError(f"Unknown anomaly detection algorithm: {self.algorithm}")

        self.is_fitted: bool = False
        self._score_min: float = 0.0
        self._score_max: float = 1.0

    def fit(self, benign_traces: Sequence[TrajectoryTrace]) -> PooledEmbeddingAnomalyBaseline:
        """Fit vectorizer and anomaly detector on benign prefix representations."""
        text_corpus: list[str] = []

        for trace in benign_traces:
            if trace.trajectory_label != "BENIGN":
                continue

            for step_idx in range(len(trace.steps)):
                inp = trace.get_pre_execution_input(step_idx)
                text_corpus.append(_format_pre_execution_text(inp))

        if not text_corpus:
            # Fallback if no benign steps exist
            text_corpus = ["Goal: benign default | Proposed: default()"]

        X = self.vectorizer.fit_transform(text_corpus).toarray()
        self.detector.fit(X)

        raw_scores = self.detector.score_samples(X)
        self._score_min = float(np.min(raw_scores))
        self._score_max = float(np.max(raw_scores))
        self.is_fitted = True
        return self

    def score_pre_execution(self, event_input: PreExecutionInput) -> float:
        """Score proposed action anomaly in [0.0, 1.0]. Higher score indicates greater anomaly."""
        if not self.is_fitted:
            return 0.5

        text = _format_pre_execution_text(event_input)
        x = self.vectorizer.transform([text]).toarray()
        raw_score = float(self.detector.score_samples(x)[0])

        # In sklearn, higher score_samples means MORE NORMAL; lower means MORE ANOMALOUS
        # We invert so higher risk score in [0, 1] means MORE ANOMALOUS
        denom = max(self._score_max - self._score_min, 1e-6)
        normalized_normality = (raw_score - self._score_min) / denom
        anomaly_score = 1.0 - normalized_normality
        return float(min(max(anomaly_score, 0.0), 1.0))

    def reset(self) -> None:
        """Reset internal state (stateless model)."""
