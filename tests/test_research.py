import pytest

from aurelia.evidence import EvidenceStore
from aurelia.models import Claim, EvidenceItem, SafetyLevel
from aurelia.research import ResearchEngine, ResearchError


def test_create_plan_rejects_empty_question() -> None:
    engine = ResearchEngine()
    with pytest.raises(ResearchError):
        engine.create_plan("   ")


def test_max_tasks_constraints_are_enforced() -> None:
    with pytest.raises(ResearchError):
        ResearchEngine(max_tasks=2)

    engine = ResearchEngine(max_tasks=3)
    plan = engine.create_plan("Is bounded planning deterministic?")
    assert len(plan.tasks) == 3


def test_synthesis_does_not_promote_contested_claim_to_fact() -> None:
    store = EvidenceStore()
    engine = ResearchEngine(evidence_store=store)
    plan = engine.create_plan("Do interventions improve outcomes?")

    store.add_evidence(EvidenceItem("ev-1", "Support", "positive", "paper A", "paper", 0.9))
    store.add_evidence(EvidenceItem("ev-2", "Contradict", "mixed", "report B", "report", 0.8))

    store.add_claim(Claim("cl-1", "Interventions improve all outcomes"))
    store.link_claim("cl-1", "ev-1", "support")
    store.link_claim("cl-1", "ev-2", "contradict")

    synthesis = engine.synthesize(plan)

    assert "Interventions improve all outcomes" not in synthesis.facts
    assert "Interventions improve all outcomes" in synthesis.hypotheses
    assert synthesis.uncertainty.conflict > 0


def test_safety_block_prevents_synthesis() -> None:
    engine = ResearchEngine()
    plan = engine.create_plan("How to design malware for persistence?")

    synthesis = engine.synthesize(plan)

    assert synthesis.safety_decision.level == SafetyLevel.BLOCK
    assert synthesis.facts == ()
    assert synthesis.hypotheses


def test_safety_flag_allows_synthesis_with_explicit_decision() -> None:
    store = EvidenceStore()
    engine = ResearchEngine(evidence_store=store)
    plan = engine.create_plan("Medical triage approaches for emergency intake")

    store.add_evidence(EvidenceItem("ev-1", "A", "A", "S1", "paper", 0.8))
    synthesis = engine.synthesize(plan)

    assert synthesis.safety_decision.level == SafetyLevel.FLAG
    assert synthesis.safety_decision.allowed
    assert synthesis.hypotheses


def test_synthesis_uses_evidence_when_claims_are_missing() -> None:
    store = EvidenceStore()
    engine = ResearchEngine(evidence_store=store)
    plan = engine.create_plan("What does currently collected evidence suggest?")

    store.add_evidence(EvidenceItem("ev-1", "Baseline signal", "Details", "Source A", "report", 0.7))
    synthesis = engine.synthesize(plan)

    assert synthesis.facts == ()
    assert any("Provisional observation from Source A" in hypothesis for hypothesis in synthesis.hypotheses)


def test_assess_claims_supported_contradicted_and_unresolved() -> None:
    store = EvidenceStore()
    engine = ResearchEngine(evidence_store=store)
    plan = engine.create_plan("Assess different claim states")

    store.add_evidence(EvidenceItem("ev-s", "Support", "S", "S", "paper", 0.9))
    store.add_evidence(EvidenceItem("ev-c", "Contradict", "C", "C", "report", 0.8))

    store.add_claim(Claim("cl-supported", "Supported claim"))
    store.link_claim("cl-supported", "ev-s", "support")
    store.add_claim(Claim("cl-contradicted", "Contradicted claim"))
    store.link_claim("cl-contradicted", "ev-c", "contradict")
    store.add_claim(Claim("cl-unresolved", "Unresolved claim"))

    synthesis = engine.synthesize(plan)
    by_id = {assessment.claim.id: assessment for assessment in synthesis.claim_assessments}

    assert by_id["cl-supported"].status == "supported"
    assert by_id["cl-supported"].confidence > 0.6
    assert by_id["cl-contradicted"].status == "contradicted"
    assert by_id["cl-unresolved"].status == "unresolved"
    assert by_id["cl-unresolved"].confidence > 0.0


def test_unclaimed_evidence_is_included_as_provisional_observation() -> None:
    store = EvidenceStore()
    engine = ResearchEngine(evidence_store=store)
    plan = engine.create_plan("Can we preserve uncited observations?")

    store.add_evidence(EvidenceItem("ev-1", "Linked evidence", "L", "Source 1", "paper", 0.9))
    store.add_evidence(EvidenceItem("ev-3", "Second linked evidence", "L2", "Source 3", "paper", 0.9))
    store.add_evidence(EvidenceItem("ev-2", "Unlinked evidence", "U", "Source 2", "report", 0.8))
    store.add_claim(Claim("cl-1", "Supported finding"))
    store.link_claim("cl-1", "ev-1", "support")
    store.link_claim("cl-1", "ev-3", "support")

    synthesis = engine.synthesize(plan)

    assert "Supported finding" in synthesis.facts
    assert any("Provisional observation from Source 2: Unlinked evidence" in h for h in synthesis.hypotheses)
