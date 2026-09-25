"""Deterministic uncertainty analysis for synthesized research outputs."""

from __future__ import annotations

from .models import ClaimAssessment, EvidenceItem, UncertaintyReport


class UncertaintyAnalyzer:
    def build_report(
        self,
        evidence: tuple[EvidenceItem, ...],
        assessments: tuple[ClaimAssessment, ...],
        assumptions: tuple[str, ...],
        open_questions: tuple[str, ...],
    ) -> UncertaintyReport:
        evidence_count = len(evidence)
        claim_count = len(assessments)

        avg_reliability = (
            sum(item.reliability for item in evidence) / evidence_count if evidence_count else 0.0
        )
        coverage = min(evidence_count / 5.0, 1.0)

        supported = sum(1 for item in assessments if item.status == "supported")
        contradicted = sum(1 for item in assessments if item.status == "contradicted")
        contested = sum(1 for item in assessments if item.status == "contested")

        agreement = supported / claim_count if claim_count else 0.0
        conflict = (contradicted + contested) / claim_count if claim_count else 0.0

        confidence = max(0.0, min(1.0, (0.45 * avg_reliability) + (0.35 * agreement) + (0.20 * coverage) - (0.25 * conflict)))

        limitations: list[str] = []
        if evidence_count < 2:
            limitations.append("Limited evidence volume")
        if avg_reliability < 0.6:
            limitations.append("Evidence quality is mixed or low")
        if conflict > 0.0:
            limitations.append("Conflicting evidence exists")
        if not limitations:
            limitations.append("No major methodological limitations identified in current scope")

        return UncertaintyReport(
            confidence=round(confidence, 3),
            evidence_coverage=round(coverage, 3),
            agreement=round(agreement, 3),
            conflict=round(conflict, 3),
            assumptions=assumptions,
            limitations=tuple(limitations),
            open_questions=open_questions,
        )
