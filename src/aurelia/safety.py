"""Conservative safety policy evaluation for research actions and outputs."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .models import SafetyDecision, SafetyLevel


@dataclass(frozen=True)
class SafetyPolicy:
    blocked_keywords: tuple[str, ...] = (
        "malware",
        "exploit",
        "weapon",
        "doxx",
        "credential theft",
        "ransomware",
    )
    flagged_keywords: tuple[str, ...] = (
        "medical",
        "legal",
        "financial",
        "critical infrastructure",
        "biometric",
    )
    high_impact_keywords: tuple[str, ...] = (
        "diagnose",
        "prescribe",
        "investment",
        "sentencing",
        "autonomous control",
    )
    pii_patterns: tuple[re.Pattern[str], ...] = field(
        default_factory=lambda: (
            re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
            re.compile(r"\b[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
            re.compile(r"\b\d{13,16}\b"),
        )
    )


class SafetyLayer:
    def __init__(self, policy: SafetyPolicy | None = None) -> None:
        self._policy = policy or SafetyPolicy()

    def evaluate(self, action: str, content: str) -> SafetyDecision:
        lowered = f"{action} {content}".lower()
        reasons: list[str] = []

        if any(term in lowered for term in self._policy.blocked_keywords):
            reasons.append("Request matches blocked harmful activity keywords")

        if any(pattern.search(content) for pattern in self._policy.pii_patterns):
            reasons.append("Content appears to include privacy-sensitive data")

        if any(term in lowered for term in self._policy.high_impact_keywords):
            reasons.append("Request may involve high-impact decision automation")

        if reasons and "blocked" in " ".join(reason.lower() for reason in reasons):
            return SafetyDecision(action=action, level=SafetyLevel.BLOCK, reasons=tuple(reasons))

        if reasons or any(term in lowered for term in self._policy.flagged_keywords):
            if not reasons:
                reasons.append("Request should be reviewed under elevated-risk policy")
            return SafetyDecision(action=action, level=SafetyLevel.FLAG, reasons=tuple(reasons))

        return SafetyDecision(action=action, level=SafetyLevel.ALLOW, reasons=("No policy concerns detected",))
