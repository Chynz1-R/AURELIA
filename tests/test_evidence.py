from aurelia.evidence import EvidenceError, EvidenceStore
from aurelia.models import Claim, EvidenceItem


def test_evidence_provenance_and_search() -> None:
    store = EvidenceStore()
    item = EvidenceItem(
        id="ev-1",
        title="Sample evidence",
        content="Structured provenance is preserved.",
        source="Source X",
        source_type="report",
        reliability=0.8,
    )
    store.add_evidence(item)

    found = store.search_evidence("provenance")
    assert found and found[0].source == "Source X"


def test_claim_support_and_contradiction_links() -> None:
    store = EvidenceStore()
    store.add_evidence(EvidenceItem("ev-1", "A", "A", "S1", "paper", 0.9))
    store.add_evidence(EvidenceItem("ev-2", "B", "B", "S2", "report", 0.7))
    store.add_claim(Claim(id="cl-1", text="Claim"))

    store.link_claim("cl-1", "ev-1", "support")
    store.link_claim("cl-1", "ev-2", "contradict")

    citations = store.list_citations_for_claim("cl-1")
    relationships = {c.relationship for c in citations}
    assert relationships == {"support", "contradict"}


def test_invalid_evidence_reliability_rejected() -> None:
    store = EvidenceStore()
    try:
        store.add_evidence(EvidenceItem("ev-1", "A", "A", "S1", "paper", 1.5))
    except EvidenceError as exc:
        assert "reliability" in str(exc)
    else:
        raise AssertionError("Expected EvidenceError")
