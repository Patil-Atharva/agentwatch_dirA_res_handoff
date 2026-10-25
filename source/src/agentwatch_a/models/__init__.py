"""Monitor models, baselines, and scoring interfaces for AgentWatch-A.

Implements Priority A baselines defined in Section 11.1 and the primary
goal-conditioned sequence monitor defined in Section 8 of AGENTWATCH_DIRECTION_A_SPEC.md:
- B1: ToolTransitionBaseline (tool-transition Markov bigram)
- B2: PooledEmbeddingAnomalyBaseline (TF-IDF prefix embeddings + Isolation Forest / OCSVM)
- B3: ContentOnlyInjectionBaseline (untrusted observation content detector, zero-action / zero-goal)
- B4: UnconditionedSequenceBaseline (unconditioned sequence model over tool calls)
- B6: SupervisedOracleBaseline (supervised step-level classifier upper bound)
- GoalConditionedGRUMonitor (primary causal goal-conditioned sequence monitor)
"""

from agentwatch_a.models.content_detector import ContentOnlyInjectionBaseline
from agentwatch_a.models.embedding_baselines import PooledEmbeddingAnomalyBaseline
from agentwatch_a.models.goal_conditioned_gru import GoalConditionedGRUMonitor
from agentwatch_a.models.interface import BaseMonitorScorer, PreExecutionInput
from agentwatch_a.models.oracle import SupervisedOracleBaseline
from agentwatch_a.models.sequence_baseline import UnconditionedSequenceBaseline
from agentwatch_a.models.transition_baseline import ToolTransitionBaseline

__all__ = [
    "BaseMonitorScorer",
    "ContentOnlyInjectionBaseline",
    "GoalConditionedGRUMonitor",
    "PooledEmbeddingAnomalyBaseline",
    "PreExecutionInput",
    "SupervisedOracleBaseline",
    "ToolTransitionBaseline",
    "UnconditionedSequenceBaseline",
]
