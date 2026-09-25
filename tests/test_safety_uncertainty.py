from aurelia.models import Claim, ClaimAssessment, EvidenceItem, SafetyLevel
from aurelia.safety import SafetyLayer
from aurelia.uncertainty import UncertaintyAnalyzer


def test_safety_flags_privacy_sensitive_content() -> None:
    decision = SafetyLayer().evaluate("summarize", "Contact me at PERSON@EXAMPLE.COM")
    assert decision.level in {SafetyLevel.FLAG, SafetyLevel.BLOCK}
    assert any("privacy" in reason.lower() for reason in decision.reasons)


def test_uncertainty_report_contains_required_fields() -> None:
    analyzer = UncertaintyAnalyzer()
    evidence = (
        EvidenceItem("ev-1", "A", "A", "S1", "paper", 0.9),
        EvidenceItem("ev-2", "B", "B", "S2", "report", 0.6),
    )
    assessments = (
        ClaimAssessment(
            claim=Claim("cl-1", "Claim"),
            supported_by=("ev-1",),
            contradicted_by=("ev-2",),
            confidence=0.55,
            status="contested",
        ),
    )

    report = analyzer.build_report(
        evidence=evidence,
        assessments=assessments,
        assumptions=("assumption",),
        open_questions=("question",),
    )

    assert 0.0 <= report.confidence <= 1.0
    assert report.evidence_coverage > 0
    assert report.agreement >= 0
    assert report.conflict >= 0
    assert report.assumptions
    assert report.limitations
    assert report.open_questions
