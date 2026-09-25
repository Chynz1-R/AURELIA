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
            re.compile(r"\b\d{3}-\d{2}-\d{4}\b", re.IGNORECASE),
            re.compile(r"\b[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}\b", re.IGNORECASE),
            re.compile(r"\b\d{13,16}\b", re.IGNORECASE),
        )
    )


class SafetyLayer:
    def __init__(self, policy: SafetyPolicy | None = None) -> None:
        self._policy = policy or SafetyPolicy()
        self._blocked_patterns = self._compile_keyword_patterns(self._policy.blocked_keywords)
        self._flagged_patterns = self._compile_keyword_patterns(self._policy.flagged_keywords)
        self._high_impact_patterns = self._compile_keyword_patterns(self._policy.high_impact_keywords)

    def evaluate(self, action: str, content: str) -> SafetyDecision:
        lowered = f"{action} {content}".lower()
        reasons: list[str] = []
        blocked_match = False
        flagged_match = False
        high_impact_match = False

        if self._contains_keyword(lowered, self._blocked_patterns):
            reasons.append("Request matches blocked harmful activity keywords")
            blocked_match = True

        if any(pattern.search(content) for pattern in self._policy.pii_patterns):
            reasons.append("Content appears to include privacy-sensitive data")

        if self._contains_keyword(lowered, self._high_impact_patterns):
            reasons.append("Request may involve high-impact decision automation")
            high_impact_match = True

        if blocked_match:
            return SafetyDecision(action=action, level=SafetyLevel.BLOCK, reasons=tuple(reasons))

        if self._contains_keyword(lowered, self._flagged_patterns):
            reasons.append("Request matches elevated-risk policy keywords")
            flagged_match = True

        if reasons or flagged_match or high_impact_match:
            if not reasons:
                reasons.append("Request should be reviewed under elevated-risk policy")
            return SafetyDecision(action=action, level=SafetyLevel.FLAG, reasons=tuple(reasons))

        return SafetyDecision(action=action, level=SafetyLevel.ALLOW, reasons=("No policy concerns detected",))

    @staticmethod
    def _compile_keyword_patterns(keywords: tuple[str, ...]) -> tuple[re.Pattern[str], ...]:
        return tuple(
            re.compile(r"\b" + r"\s+".join(re.escape(part) for part in keyword.split()) + r"\b")
            for keyword in keywords
        )

    @staticmethod
    def _contains_keyword(text: str, patterns: tuple[re.Pattern[str], ...]) -> bool:
        for pattern in patterns:
            if pattern.search(text):
                return True
        return False
