"""In-memory evidence storage and claim linkage."""

from __future__ import annotations

from dataclasses import replace

from .models import Claim, Citation, EvidenceItem


class EvidenceError(ValueError):
    """Raised when evidence or claim operations are invalid."""


class EvidenceStore:
    def __init__(self) -> None:
        self._evidence: dict[str, EvidenceItem] = {}
        self._claims: dict[str, Claim] = {}
        self._citations: list[Citation] = []

    def add_evidence(self, item: EvidenceItem) -> None:
        if not item.id:
            raise EvidenceError("Evidence id is required")
        if not item.source:
            raise EvidenceError("Evidence source is required")
        if not (0.0 <= item.reliability <= 1.0):
            raise EvidenceError("Evidence reliability must be between 0.0 and 1.0")
        self._evidence[item.id] = item

    def get_evidence(self, evidence_id: str) -> EvidenceItem | None:
        return self._evidence.get(evidence_id)

    def list_evidence(self) -> tuple[EvidenceItem, ...]:
        return tuple(sorted(self._evidence.values(), key=lambda item: item.collected_at))

    def search_evidence(self, text: str) -> tuple[EvidenceItem, ...]:
        query = text.strip().lower()
        if not query:
            return ()
        results = [
            item
            for item in self._evidence.values()
            if query in item.title.lower() or query in item.content.lower() or query in item.source.lower()
        ]
        return tuple(sorted(results, key=lambda item: item.collected_at))

    def add_claim(self, claim: Claim) -> None:
        if not claim.id:
            raise EvidenceError("Claim id is required")
        if not claim.text.strip():
            raise EvidenceError("Claim text is required")
        self._claims[claim.id] = replace(claim, text=claim.text.strip())

    def link_claim(self, claim_id: str, evidence_id: str, relationship: str) -> None:
        if claim_id not in self._claims:
            raise EvidenceError(f"Unknown claim id: {claim_id}")
        if evidence_id not in self._evidence:
            raise EvidenceError(f"Unknown evidence id: {evidence_id}")
        relation = relationship.strip().lower()
        if relation not in {"support", "contradict"}:
            raise EvidenceError("Relationship must be 'support' or 'contradict'")
        self._citations.append(Citation(claim_id=claim_id, evidence_id=evidence_id, relationship=relation))

    def list_claims(self) -> tuple[Claim, ...]:
        return tuple(self._claims.values())

    def list_citations_for_claim(self, claim_id: str) -> tuple[Citation, ...]:
        return tuple(c for c in self._citations if c.claim_id == claim_id)
