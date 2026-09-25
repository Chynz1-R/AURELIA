import pytest

from aurelia.evidence import EvidenceStore
from aurelia.models import Claim, EvidenceItem, SafetyLevel
from aurelia.research import ResearchEngine, ResearchError


def test_create_plan_rejects_empty_question() -> None:
    engine = ResearchEngine()
    with pytest.raises(ResearchError):
        engine.create_plan("   ")


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
