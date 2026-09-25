"""Typed domain models for AURELIA."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SafetyLevel(str, Enum):
    ALLOW = "allow"
    FLAG = "flag"
    BLOCK = "block"


@dataclass(frozen=True)
class ResearchQuestion:
    text: str
    context: str = ""
    created_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class ResearchTask:
    id: str
    description: str
    rationale: str


@dataclass(frozen=True)
class ResearchPlan:
    question: ResearchQuestion
    tasks: tuple[ResearchTask, ...]
    assumptions: tuple[str, ...]
    limitations: tuple[str, ...]
    created_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class EvidenceItem:
    id: str
    title: str
    content: str
    source: str
    source_type: str
    reliability: float
    collected_at: datetime = field(default_factory=utc_now)
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Claim:
    id: str
    text: str
    created_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class Citation:
    claim_id: str
    evidence_id: str
    relationship: str


@dataclass(frozen=True)
class ClaimAssessment:
    claim: Claim
    supported_by: tuple[str, ...]
    contradicted_by: tuple[str, ...]
    confidence: float
    status: str


@dataclass(frozen=True)
class SafetyDecision:
    action: str
    level: SafetyLevel
    reasons: tuple[str, ...]

    @property
    def allowed(self) -> bool:
        return self.level != SafetyLevel.BLOCK


@dataclass(frozen=True)
class UncertaintyReport:
    confidence: float
    evidence_coverage: float
    agreement: float
    conflict: float
    assumptions: tuple[str, ...]
    limitations: tuple[str, ...]
    open_questions: tuple[str, ...]


@dataclass(frozen=True)
class ResearchSynthesis:
    question: ResearchQuestion
    plan: ResearchPlan
    safety_decision: SafetyDecision
    facts: tuple[str, ...]
    hypotheses: tuple[str, ...]
    claim_assessments: tuple[ClaimAssessment, ...]
    uncertainty: UncertaintyReport
