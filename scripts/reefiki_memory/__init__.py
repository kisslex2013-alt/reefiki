from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
import re
from typing import Any


class ProviderCapability(StrEnum):
    READ = "read"
    WRITE_DRAFT = "write_draft"
    SEARCH = "search"
    PROMOTE_SOURCE = "promote_source"
    HEALTH = "health"
    PROVENANCE = "provenance"
    RELATED_SUGGESTIONS = "related_suggestions"


@dataclass(frozen=True)
class ProviderDescriptor:
    id: str
    kind: str
    capabilities: list[ProviderCapability]
    root: str | None = None
    status: str = "available"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "capabilities": [str(capability) for capability in self.capabilities],
            "root": self.root,
            "status": self.status,
        }


@dataclass(frozen=True)
class ProviderRegistry:
    providers: dict[str, ProviderDescriptor]

    def to_dict(self) -> dict[str, Any]:
        return {
            "providers": {
                provider_id: provider.to_dict()
                for provider_id, provider in sorted(self.providers.items())
            }
        }


@dataclass(frozen=True)
class RouteDecision:
    recommended_layer: str
    reason: str
    target_project: str | None = None
    secondary_layers: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)
    needs_user_confirmation: bool = False
    input_hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_hash": self.input_hash,
            "recommended_layer": self.recommended_layer,
            "secondary_layers": list(self.secondary_layers),
            "reason": self.reason,
            "target_project": self.target_project,
            "risk_flags": list(self.risk_flags),
            "needs_user_confirmation": self.needs_user_confirmation,
        }


@dataclass(frozen=True)
class LookupResult:
    id: str
    layer: str
    project: str | None
    title: str
    kind: str
    path: str | None
    summary: str
    provenance: str | None = None
    freshness: str = "unknown"
    confidence: str = "unknown"
    next_action: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "layer": self.layer,
            "project": self.project,
            "title": self.title,
            "kind": self.kind,
            "path": self.path,
            "summary": self.summary,
            "provenance": self.provenance,
            "freshness": self.freshness,
            "confidence": self.confidence,
            "next_action": self.next_action,
        }


@dataclass(frozen=True)
class PromotionCandidate:
    content: str
    source_layer: str
    target_project: str
    suggested_action: str
    target_type: str | None = None
    duplicate_candidates: list[str] = field(default_factory=list)
    review_state: str = "needs_review"

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "source_layer": self.source_layer,
            "target_project": self.target_project,
            "suggested_action": self.suggested_action,
            "target_type": self.target_type,
            "duplicate_candidates": list(self.duplicate_candidates),
            "review_state": self.review_state,
        }


@dataclass(frozen=True)
class AccessBoundaryContext:
    project: str
    allowed_scopes: list[str]
    forbidden_scopes: list[str]
    visibility: str = "private"
    agent_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "allowed_scopes": list(self.allowed_scopes),
            "forbidden_scopes": list(self.forbidden_scopes),
            "visibility": self.visibility,
            "agent_id": self.agent_id,
        }


@dataclass(frozen=True)
class PolicyPreflightResult:
    operation: str
    outcome: str
    blocking_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checked_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "outcome": self.outcome,
            "blocking_reasons": list(self.blocking_reasons),
            "warnings": list(self.warnings),
            "checked_paths": list(self.checked_paths),
        }


class PolicySafetyLayer:
    SECRET_PATTERNS = [
        re.compile(r"(?i)\b(api[_-]?key|token|password|secret)\b\s*[:=]\s*\S+"),
        re.compile(r"\btvly-dev-[A-Za-z0-9]{8,}\b"),
        re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    ]

    def preflight(
        self,
        boundary: AccessBoundaryContext,
        operation: str,
        content: str = "",
        paths: list[str] | None = None,
    ) -> PolicyPreflightResult:
        checked_paths = [self._normalize_path(path) for path in (paths or [])]
        blocking_reasons: list[str] = []
        warnings: list[str] = []

        for path in checked_paths:
            for forbidden in boundary.forbidden_scopes:
                if self._path_matches_scope(path, forbidden):
                    blocking_reasons.append(f"forbidden_scope:{forbidden}")
            if boundary.allowed_scopes and not any(
                self._path_matches_scope(path, allowed)
                for allowed in boundary.allowed_scopes
            ):
                blocking_reasons.append("outside_allowed_scopes")

        if any(pattern.search(content) for pattern in self.SECRET_PATTERNS):
            blocking_reasons.append("secret_like_content")

        if boundary.visibility == "public":
            warnings.append("public_visibility_requires_explicit_review")

        return PolicyPreflightResult(
            operation=operation,
            outcome="block" if blocking_reasons else "pass",
            blocking_reasons=sorted(set(blocking_reasons)),
            warnings=sorted(set(warnings)),
            checked_paths=checked_paths,
        )

    @staticmethod
    def _normalize_path(path: str) -> str:
        return path.replace("\\", "/").strip("/")

    @classmethod
    def _path_matches_scope(cls, path: str, scope: str) -> bool:
        normalized_scope = cls._normalize_path(scope)
        return path == normalized_scope or path.startswith(normalized_scope + "/")


@dataclass(frozen=True)
class MemoryDecisionTrace:
    operation: str
    boundary_context: AccessBoundaryContext
    route_decision: RouteDecision
    policy_checks: list[dict[str, Any]] = field(default_factory=list)
    lookup_results: list[LookupResult] = field(default_factory=list)
    promotion_candidates: list[PromotionCandidate] = field(default_factory=list)
    safety_outcome: str = "pass"
    trace_id: str | None = None
    input_hash: str | None = None
    created_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "operation": self.operation,
            "input_hash": self.input_hash,
            "boundary_context": self.boundary_context.to_dict(),
            "route_decision": self.route_decision.to_dict(),
            "policy_checks": list(self.policy_checks),
            "lookup_results": [result.to_dict() for result in self.lookup_results],
            "promotion_candidates": [
                candidate.to_dict() for candidate in self.promotion_candidates
            ],
            "safety_outcome": self.safety_outcome,
            "created_at": self.created_at,
        }


def build_default_registry(project_root: Path) -> ProviderRegistry:
    project_root_text = str(project_root)
    return ProviderRegistry(
        providers={
            "reefiki": ProviderDescriptor(
                id="reefiki",
                kind="markdown-wiki",
                root=str(project_root / "wiki"),
                capabilities=[
                    ProviderCapability.READ,
                    ProviderCapability.WRITE_DRAFT,
                    ProviderCapability.SEARCH,
                    ProviderCapability.PROMOTE_SOURCE,
                    ProviderCapability.HEALTH,
                    ProviderCapability.PROVENANCE,
                ],
            ),
            "memoir": ProviderDescriptor(
                id="memoir",
                kind="working-memory",
                root=project_root_text,
                capabilities=[
                    ProviderCapability.READ,
                    ProviderCapability.SEARCH,
                    ProviderCapability.PROMOTE_SOURCE,
                    ProviderCapability.HEALTH,
                    ProviderCapability.PROVENANCE,
                ],
            ),
            "graphify": ProviderDescriptor(
                id="graphify",
                kind="structure-graph",
                root=project_root_text,
                capabilities=[
                    ProviderCapability.READ,
                    ProviderCapability.SEARCH,
                    ProviderCapability.HEALTH,
                    ProviderCapability.PROVENANCE,
                    ProviderCapability.RELATED_SUGGESTIONS,
                ],
            ),
        }
    )
