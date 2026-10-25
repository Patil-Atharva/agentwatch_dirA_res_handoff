"""Deterministic text and tool encoding for AgentWatch-A models.

Adheres strictly to Section 8.3 and Section 8.4 of AGENTWATCH_DIRECTION_A_SPEC.md.
Extracts fixed-dimensional representations for goals, actions, and observations
using a lightweight, zero-cost, local PyTorch architecture.
"""

from __future__ import annotations

import json
import re
import zlib
from typing import Any

import torch
from torch import nn

TOKEN_REGEX = re.compile(r"\b\w+\b")

# Canonical tools in AgentDojo workspace environment
CANONICAL_TOOLS: list[str] = [
    "<UNK>",
    "<START>",
    "search_contacts_by_name",
    "send_email",
    "get_unread_emails",
    "get_received_emails",
    "search_emails",
    "delete_email",
    "search_calendar_events",
    "reschedule_calendar_event",
    "cancel_calendar_event",
    "search_files",
    "get_file_by_id",
    "list_files",
    "create_file",
    "delete_file",
    "share_file",
    "append_to_file",
]


class DeterministicTextEncoder(nn.Module):
    """Encodes arbitrary text into a fixed dense representation via hashed token embeddings.

    Guarantees deterministic, bounded, zero-cost offline embedding without cloud dependencies.
    """

    def __init__(self, vocab_buckets: int = 1024, embedding_dim: int = 64):
        super().__init__()
        self.vocab_buckets = vocab_buckets
        self.embedding_dim = embedding_dim
        self.embedding_bag = nn.EmbeddingBag(
            num_embeddings=vocab_buckets,
            embedding_dim=embedding_dim,
            mode="mean",
        )

    def _tokenize_to_ids(self, text: str) -> list[int]:
        """Deterministic token hashing to vocabulary bucket IDs."""
        if not text:
            return [0]
        tokens = TOKEN_REGEX.findall(text.lower())
        if not tokens:
            return [0]
        # Hash each token deterministically into [0, vocab_buckets - 1]
        return [zlib.crc32(t.encode("utf-8")) % self.vocab_buckets for t in tokens]

    def forward(self, texts: list[str]) -> torch.Tensor:
        """Encode a batch of strings into Tensor of shape (batch_size, embedding_dim)."""
        if not texts:
            return torch.zeros((0, self.embedding_dim), dtype=torch.float32)

        indices_list: list[int] = []
        offsets: list[int] = []
        curr_offset = 0

        for text in texts:
            token_ids = self._tokenize_to_ids(text)
            offsets.append(curr_offset)
            indices_list.extend(token_ids)
            curr_offset += len(token_ids)

        indices = torch.tensor(indices_list, dtype=torch.long)
        offsets_tensor = torch.tensor(offsets, dtype=torch.long)
        return self.embedding_bag(indices, offsets_tensor)


class ToolActionEncoder(nn.Module):
    """Encodes a proposed tool action (tool_name, arguments) into a dense representation."""

    def __init__(
        self,
        tool_embedding_dim: int = 32,
        args_embedding_dim: int = 32,
    ):
        super().__init__()
        self.tool_to_id: dict[str, int] = {tool: idx for idx, tool in enumerate(CANONICAL_TOOLS)}
        self.tool_embedding = nn.Embedding(len(CANONICAL_TOOLS), tool_embedding_dim)
        self.text_encoder = DeterministicTextEncoder(embedding_dim=args_embedding_dim)
        self.total_dim = tool_embedding_dim + args_embedding_dim + 2  # + num_args + len_args

    def get_tool_id(self, tool_name: str) -> int:
        """Lookup tool integer ID with fallback to <UNK>."""
        return self.tool_to_id.get(tool_name, 0)

    def forward(self, tool_names: list[str], args_list: list[dict[str, Any]]) -> torch.Tensor:
        """Encode proposed actions into Tensor of shape (batch_size, total_dim)."""
        batch_size = len(tool_names)
        if batch_size == 0:
            return torch.zeros((0, self.total_dim), dtype=torch.float32)

        tool_ids = [self.get_tool_id(t) for t in tool_names]
        tool_ids_tensor = torch.tensor(tool_ids, dtype=torch.long)
        tool_emb = self.tool_embedding(tool_ids_tensor)  # (batch_size, tool_dim)

        # Serialize arguments to JSON strings
        args_texts = [json.dumps(args, sort_keys=True) for args in args_list]
        args_emb = self.text_encoder(args_texts)  # (batch_size, args_dim)

        # Numerical argument features: count and length normalized
        num_args = torch.tensor([[float(len(a))] for a in args_list], dtype=torch.float32)
        len_args = torch.tensor([[float(len(t)) / 100.0] for t in args_texts], dtype=torch.float32)

        return torch.cat([tool_emb, args_emb, num_args, len_args], dim=-1)
