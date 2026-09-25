"""Research orchestration engine."""

from __future__ import annotations

from dataclasses import replace

from .evidence import EvidenceStore
from .models import (
    ClaimAssessment,
    EvidenceItem,
    ResearchPlan,
    ResearchQuestion,
    ResearchSynthesis,
    ResearchTask,
)
from .safety import SafetyLayer
from .uncertainty import UncertaintyAnalyzer


class ResearchError(ValueError):
    """Raised when the research engine encounters invalid inputs."""


class ResearchEngine:
    def __init__(
        self,
        evidence_store: EvidenceStore | None = None,
        safety_layer: SafetyLayer | None = None,
        uncertainty_analyzer: UncertaintyAnalyzer | None = None,
        max_tasks: int = 5,
    ) -> None:
        if max_tasks < 3:
            raise ResearchError("max_tasks must be at least 3")
        self.evidence_store = evidence_store or EvidenceStore()
        self.safety_layer = safety_layer or SafetyLayer()
        self.uncertainty_analyzer = uncertainty_analyzer or UncertaintyAnalyzer()
        self.max_tasks = max_tasks

    def create_plan(self, question_text: str, context: str = "") -> ResearchPlan:
        clean_question = question_text.strip()
        if not clean_question:
            raise ResearchError("Research question cannot be empty")
        if len(clean_question) > 500:
            raise ResearchError("Research question is too long")

        question = ResearchQuestion(text=clean_question, context=context.strip())
        tasks = (
            ResearchTask("scope", "Define operational scope and key terms", "Prevents ambiguous conclusions"),
            ResearchTask("collect", "Collect at least two independent evidence sources", "Improves coverage"),
            ResearchTask("challenge", "Identify contradictory or alternative explanations", "Avoids one-sided conclusions"),
            ResearchTask("synthesize", "Synthesize findings with explicit uncertainty", "Separates fact from hypothesis"),
            ResearchTask("gaps", "List unresolved questions and next evidence needs", "Supports iterative investigation"),
        )[: self.max_tasks]

        assumptions = (
            "Available evidence may be incomplete",
            "Source reliability estimates are approximate",
        )
        limitations = (
            "No network actions are executed by the engine",
            "Outputs are advisory and require human review for high-impact decisions",
        )

        return ResearchPlan(question=question, tasks=tasks, assumptions=assumptions, limitations=limitations)

    def add_evidence(self, item: EvidenceItem) -> None:
        self.evidence_store.add_evidence(item)

    def assess_claims(self) -> tuple[ClaimAssessment, ...]:
        assessments: list[ClaimAssessment] = []
        for claim in self.evidence_store.list_claims():
            citations = self.evidence_store.list_citations_for_claim(claim.id)
            supported = tuple(c.evidence_id for c in citations if c.relationship == "support")
            contradicted = tuple(c.evidence_id for c in citations if c.relationship == "contradict")

            if supported and not contradicted:
                status = "supported"
            elif contradicted and not supported:
                status = "contradicted"
            elif supported and contradicted:
                status = "contested"
            else:
                status = "unresolved"

            confidence = self._claim_confidence(supported, contradicted)
            assessments.append(
                ClaimAssessment(
                    claim=replace(claim),
                    supported_by=supported,
                    contradicted_by=contradicted,
                    confidence=confidence,
                    status=status,
                )
            )

        return tuple(assessments)

    def synthesize(self, plan: ResearchPlan) -> ResearchSynthesis:
        safety_decision = self.safety_layer.evaluate("research_synthesis", plan.question.text)
        if not safety_decision.allowed:
            empty_report = self.uncertainty_analyzer.build_report((), (), plan.assumptions, ("Synthesis blocked by safety policy",))
            return ResearchSynthesis(
                question=plan.question,
                plan=plan,
                safety_decision=safety_decision,
                facts=(),
                hypotheses=("Synthesis was blocked and no conclusions were generated.",),
                claim_assessments=(),
                uncertainty=empty_report,
            )

        evidence = self.evidence_store.list_evidence()
        assessments = self.assess_claims()

        facts: list[str] = []
        hypotheses: list[str] = []
        cited_evidence_ids: set[str] = set()
        for assessment in assessments:
            cited_evidence_ids.update(assessment.supported_by)
            cited_evidence_ids.update(assessment.contradicted_by)
            if assessment.status == "supported" and assessment.confidence >= 0.7:
                facts.append(assessment.claim.text)
            else:
                hypotheses.append(assessment.claim.text)

        for item in evidence:
            if item.id not in cited_evidence_ids:
                hypotheses.append(f"Provisional observation from {item.source}: {item.title}")

        if not facts and not assessments:
            hypotheses.append(f"Insufficient claim evidence to establish facts for: {plan.question.text}")

        open_questions = self._open_questions(plan, evidence, assessments)
        uncertainty = self.uncertainty_analyzer.build_report(
            evidence=evidence,
            assessments=assessments,
            assumptions=plan.assumptions,
            open_questions=open_questions,
        )

        return ResearchSynthesis(
            question=plan.question,
            plan=plan,
            safety_decision=safety_decision,
            facts=tuple(facts),
            hypotheses=tuple(hypotheses),
            claim_assessments=assessments,
            uncertainty=uncertainty,
        )

    def _claim_confidence(self, supported: tuple[str, ...], contradicted: tuple[str, ...]) -> float:
        support_reliability = self._average_reliability(supported)
        contradiction_reliability = self._average_reliability(contradicted)
        support_score = min(len(supported), 3) / 3.0
        contradiction_score = min(len(contradicted), 3) / 3.0
        confidence = (
            0.2
            + (0.45 * support_reliability)
            + (0.25 * support_score)
            - (0.30 * contradiction_reliability)
            - (0.20 * contradiction_score)
        )
        return round(max(0.0, min(1.0, confidence)), 3)

    def _average_reliability(self, evidence_ids: tuple[str, ...]) -> float:
        if not evidence_ids:
            return 0.0
        reliabilities = [
            evidence.reliability
            for evidence_id in evidence_ids
            if (evidence := self.evidence_store.get_evidence(evidence_id)) is not None
        ]
        return sum(reliabilities) / len(reliabilities) if reliabilities else 0.0

    def _open_questions(
        self,
        plan: ResearchPlan,
        evidence: tuple[EvidenceItem, ...],
        assessments: tuple[ClaimAssessment, ...],
    ) -> tuple[str, ...]:
        questions: list[str] = []
        if len(evidence) < 2:
            questions.append("What additional independent evidence can be collected?")
        if any(a.status in {"contested", "unresolved"} for a in assessments):
            questions.append("How can contested claims be resolved with stronger sources?")
        if not questions:
            questions.append("Which assumptions should be stress-tested next?")
        if plan.tasks:
            questions.append(f"Which task from plan remains least supported? ({plan.tasks[-1].id})")
        else:
            questions.append("Which research task should be defined next?")
        return tuple(questions)
