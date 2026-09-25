"""Minimal CLI demo for AURELIA."""

from __future__ import annotations

import argparse
import json

from .evidence import EvidenceStore
from .models import Claim, EvidenceItem
from .research import ResearchEngine


def run_demo(question: str) -> dict[str, object]:
    store = EvidenceStore()
    engine = ResearchEngine(evidence_store=store)
    plan = engine.create_plan(question)

    store.add_evidence(
        EvidenceItem(
            id="ev-1",
            title="Peer-reviewed baseline",
            content="Initial studies show measurable improvements under controlled conditions.",
            source="Journal A",
            source_type="paper",
            reliability=0.85,
        )
    )
    store.add_evidence(
        EvidenceItem(
            id="ev-2",
            title="Field report",
            content="A later field report observed mixed outcomes across regions.",
            source="Agency B",
            source_type="report",
            reliability=0.65,
        )
    )

    store.add_claim(Claim(id="cl-1", text="The intervention improves outcomes in all contexts"))
    store.link_claim("cl-1", "ev-1", "support")
    store.link_claim("cl-1", "ev-2", "contradict")

    synthesis = engine.synthesize(plan)

    return {
        "question": synthesis.question.text,
        "safety": synthesis.safety_decision.level.value,
        "facts": list(synthesis.facts),
        "hypotheses": list(synthesis.hypotheses),
        "uncertainty": {
            "confidence": synthesis.uncertainty.confidence,
            "coverage": synthesis.uncertainty.evidence_coverage,
            "agreement": synthesis.uncertainty.agreement,
            "conflict": synthesis.uncertainty.conflict,
            "limitations": list(synthesis.uncertainty.limitations),
            "open_questions": list(synthesis.uncertainty.open_questions),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="AURELIA local research demo")
    parser.add_argument("question", nargs="?", default="How reliable is the proposed intervention?")
    args = parser.parse_args()

    result = run_demo(args.question)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
