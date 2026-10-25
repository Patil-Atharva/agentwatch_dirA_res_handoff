"""Goal-conditioned causal sequence monitor (GRU).

Adheres strictly to Section 8.5, Section 8.6, and Section 8.7 of AGENTWATCH_DIRECTION_A_SPEC.md.
A lightweight, causal, online pre-execution monitor evaluating goal-action alignment
and argument provenance to detect indirect prompt injection hijacks before tool execution.
"""

from __future__ import annotations

from typing import Any

import torch
import torch.nn.functional as F
from torch import nn

from agentwatch_a.features.text_encoder import DeterministicTextEncoder, ToolActionEncoder
from agentwatch_a.models.interface import BaseMonitorScorer, PreExecutionInput
from agentwatch_a.provenance import extract_provenance_features


def _extract_provenance_vector(event_input: PreExecutionInput, mask_goal: bool = False) -> list[float]:
    """Extract Section 8.7 numerical provenance vector (dimension 7)."""
    prov = extract_provenance_features(event_input)
    num_args = max(float(prov.num_arguments), 1.0)
    in_goal = 0.0 if mask_goal else float(prov.num_arguments_in_goal)
    from_untrusted = float(prov.num_arguments_from_untrusted)

    return [
        1.0 if prov.high_impact_tool else 0.0,
        1.0 if prov.high_impact_untrusted_argument else 0.0,
        float(prov.num_arguments),
        in_goal,
        from_untrusted,
        in_goal / num_args,
        from_untrusted / num_args,
    ]


class GoalConditionedGRUMonitor(BaseMonitorScorer, nn.Module):
    """Primary Goal-Conditioned Causal Sequence Monitor.

    Evaluates the causal prefix u_t = (g, (a_1, o_1), ..., (a_{t-1}, o_{t-1}), a_t)
    at the pre-execution boundary, producing risk score R_t in [0.0, 1.0].
    """

    def __init__(
        self,
        goal_dim: int = 64,
        hidden_dim: int = 64,
        proj_dim: int = 32,
        ablation_no_goal: bool = False,
    ):
        nn.Module.__init__(self)
        self.goal_dim = goal_dim
        self.hidden_dim = hidden_dim
        self.proj_dim = proj_dim
        self.ablation_no_goal = ablation_no_goal

        # 1. Feature encoders
        self.goal_encoder = DeterministicTextEncoder(embedding_dim=goal_dim)
        self.action_encoder = ToolActionEncoder(tool_embedding_dim=32, args_embedding_dim=32)
        self.obs_encoder = DeterministicTextEncoder(embedding_dim=32)

        # 2. Step input projection: action_dim (66) + obs_dim (32) + prov_dim (7) = 105
        step_input_dim = self.action_encoder.total_dim + 32 + 7
        self.step_proj = nn.Linear(step_input_dim, hidden_dim)

        # 3. Causal recurrent core
        self.gru = nn.GRU(input_size=hidden_dim, hidden_size=hidden_dim, batch_first=True)
        self.goal_init_proj = nn.Linear(goal_dim, hidden_dim)

        # 4. Projections for goal-action compatibility
        self.proj_goal = nn.Linear(goal_dim, proj_dim)
        self.proj_step = nn.Linear(hidden_dim, proj_dim)

        # 5. Risk scoring head combining representation compatibility and provenance
        self.risk_head = nn.Sequential(
            nn.Linear(1 + hidden_dim + 7, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid(),
        )

        self.reset()

    def encode_goal(self, goal: str) -> torch.Tensor:
        """Encode user goal into goal representation (1, goal_dim)."""
        if self.ablation_no_goal:
            return torch.zeros((1, self.goal_dim), dtype=torch.float32)
        return self.goal_encoder([goal])

    def encode_step_input(
        self,
        tool: str,
        args: dict[str, Any],
        recent_obs: str,
        prov_vec: list[float],
    ) -> torch.Tensor:
        """Encode single decision step into input vector (1, hidden_dim)."""
        action_emb = self.action_encoder([tool], [args])  # (1, 66)
        obs_emb = self.obs_encoder([recent_obs])  # (1, 32)
        prov_tensor = torch.tensor([prov_vec], dtype=torch.float32)  # (1, 7)

        raw_step = torch.cat([action_emb, obs_emb, prov_tensor], dim=-1)
        return F.relu(self.step_proj(raw_step))  # (1, hidden_dim)

    def compute_step_risk(
        self,
        goal_emb: torch.Tensor,
        hidden_state: torch.Tensor,
        prov_vec: list[float],
    ) -> float:
        """Compute risk score R_t in [0.0, 1.0] from current GRU state and goal."""
        z_g = F.normalize(self.proj_goal(goal_emb), p=2, dim=-1)
        z_t = F.normalize(self.proj_step(hidden_state), p=2, dim=-1)

        if self.ablation_no_goal:
            compat = torch.zeros((1, 1), dtype=torch.float32)
        else:
            cosine_sim = torch.sum(z_g * z_t, dim=-1, keepdim=True)  # in [-1, 1]
            compat = (cosine_sim + 1.0) / 2.0  # in [0, 1]

        incompat = 1.0 - compat
        prov_tensor = torch.tensor([prov_vec], dtype=torch.float32)

        feat = torch.cat([incompat, hidden_state, prov_tensor], dim=-1)
        raw_risk = self.risk_head(feat)

        is_high_impact_taint = prov_vec[1] > 0.5
        score = raw_risk.item()
        if is_high_impact_taint:
            score = max(score, 0.85)

        return float(min(max(score, 0.0), 1.0))

    def score_pre_execution(self, event_input: PreExecutionInput) -> float:
        """Score proposed tool action at pre-execution decision boundary.

        Strictly enforces Section 6.1: zero access to current observation o_t,
        zero future steps, and zero ground-truth labels.
        """
        goal = event_input.goal
        goal_emb = self.encode_goal(goal)

        # Initialize hidden state h_0
        if self.ablation_no_goal:
            h = torch.zeros((1, 1, self.hidden_dim), dtype=torch.float32)
        else:
            h = torch.tanh(self.goal_init_proj(goal_emb)).unsqueeze(0)

        # Causal prefix unrolling: steps 0 to t-1
        for i, prior_act in enumerate(event_input.prior_actions):
            p_tool = prior_act.get("tool", "")
            p_args = prior_act.get("args", {})
            p_obs = event_input.prior_observations[i] if i < len(event_input.prior_observations) else ""

            partial_input = PreExecutionInput(
                goal=goal,
                step_index=i,
                prior_actions=event_input.prior_actions[:i],
                prior_observations=event_input.prior_observations[:i],
                proposed_tool=p_tool,
                proposed_args=p_args,
            )
            p_prov = _extract_provenance_vector(partial_input, mask_goal=self.ablation_no_goal)
            x_i = self.encode_step_input(p_tool, p_args, p_obs, p_prov).unsqueeze(1)
            _, h = self.gru(x_i, h)

        # Current proposed action step t
        curr_tool = event_input.proposed_tool
        curr_args = event_input.proposed_args
        recent_obs = event_input.prior_observations[-1] if event_input.prior_observations else ""
        curr_prov = _extract_provenance_vector(event_input, mask_goal=self.ablation_no_goal)

        x_curr = self.encode_step_input(curr_tool, curr_args, recent_obs, curr_prov).unsqueeze(1)
        _, h_curr = self.gru(x_curr, h)

        # Compute risk score from causal hidden state
        return self.compute_step_risk(goal_emb, h_curr.squeeze(0), curr_prov)

    def reset(self) -> None:
        """Reset internal causal sequential state between trajectories."""
