from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from typing import Iterable

__all__ = [
    "GovernanceIssue",
    "GovernanceResult",
    "GovernancePolicy",
    "evaluate_prompt",
    "validate_prompt",
    "main",
    "__version__",
]

__version__ = "0.1.0"


@dataclass(frozen=True)
class GovernanceIssue:
    """A single governance concern identified during AI usage review."""

    category: str
    severity: str
    description: str
    recommended_action: str = ""


@dataclass
class GovernanceResult:
    """The outcome of evaluating a prompt or model interaction."""

    approved: bool
    issues: list[GovernanceIssue] = field(default_factory=list)
    risk_level: str = "low"

    @property
    def has_issues(self) -> bool:
        return bool(self.issues)


class GovernancePolicy:
    """A lightweight, configurable AI governance policy.

    The policy performs deterministic checks to surface risky prompts before they are
    sent to an AI system. It is intentionally small and dependency-free so it can be
    used in tests, scripts, and onboarding workflows.
    """

    HIGH_RISK_KEYWORDS = {
        "bypass",
        "exfiltrate",
        "inject",
        "malware",
        "password",
        "secret",
        "token",
        "credential",
        "exploit",
        "phishing",
        "spam",
        "delete data",
        "dump database",
    }

    MEDIUM_RISK_KEYWORDS = {
        "financial",
        "medical",
        "legal",
        "sensitive",
        "private",
        "customer data",
        "government",
        "export control",
        "security",
    }

    def __init__(
        self,
        *,
        require_human_review: bool = True,
        sensitive_terms: Iterable[str] | None = None,
    ) -> None:
        self.require_human_review = require_human_review
        self.sensitive_terms = {
            *self.MEDIUM_RISK_KEYWORDS,
            *(sensitive_terms or ()),
        }

    def _severity_for(self, text: str) -> str:
        normalized = text.lower()
        if any(keyword in normalized for keyword in self.HIGH_RISK_KEYWORDS):
            return "high"
        if any(keyword in normalized for keyword in self.sensitive_terms):
            return "medium"
        return "low"

    def evaluate(self, prompt: str, *, model: str | None = None, risk_level: str = "low") -> GovernanceResult:
        """Evaluate a prompt according to the stored governance rules."""
        if not isinstance(prompt, str):
            raise TypeError("prompt must be a string")

        prompt_text = prompt.strip()
        issues: list[GovernanceIssue] = []
        normalized_risk = risk_level.strip().lower()

        if not prompt_text:
            issues.append(
                GovernanceIssue(
                    category="input",
                    severity="medium",
                    description="Prompt is empty.",
                    recommended_action="Provide a clear prompt before submitting it for review.",
                )
            )

        if model and model.strip() == "":
            issues.append(
                GovernanceIssue(
                    category="configuration",
                    severity="low",
                    description="Model name is empty.",
                    recommended_action="Specify the model name to make the review traceable.",
                )
            )

        for keyword in sorted(self.HIGH_RISK_KEYWORDS):
            if keyword in prompt_text.lower():
                issues.append(
                    GovernanceIssue(
                        category="content",
                        severity="high",
                        description=f"Prompt includes high-risk keyword: '{keyword}'.",
                        recommended_action="Escalate for human review and confirm that the request is appropriate and authorized.",
                    )
                )
                break

        for keyword in sorted(self.sensitive_terms):
            if keyword in prompt_text.lower():
                issues.append(
                    GovernanceIssue(
                        category="content",
                        severity="medium",
                        description=f"Prompt includes sensitive-term keyword: '{keyword}'.",
                        recommended_action="Verify access controls, data handling requirements, and review permissions before execution.",
                    )
                )
                break

        if normalized_risk == "high" and not issues:
            issues.append(
                GovernanceIssue(
                    category="risk",
                    severity="medium",
                    description="Risk level is marked as high but no specific issues were detected.",
                    recommended_action="Confirm the risk classification with the responsible reviewer.",
                )
            )

        approved = not issues or not self.require_human_review
        return GovernanceResult(
            approved=approved,
            issues=issues,
            risk_level=max((normalized_risk, self._severity_for(prompt_text)), key=lambda item: (item == "high", item == "medium")),
        )


def evaluate_prompt(prompt: str, *, model: str | None = None, risk_level: str = "low") -> GovernanceResult:
    """Convenience wrapper for evaluating a prompt using the default policy."""
    return GovernancePolicy().evaluate(prompt, model=model, risk_level=risk_level)


def validate_prompt(prompt: str, *, model: str | None = None, risk_level: str = "low") -> list[str]:
    """Return a list of human-readable issue messages for a prompt."""
    result = evaluate_prompt(prompt, model=model, risk_level=risk_level)
    return [issue.description for issue in result.issues]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Assess AI governance risk for a prompt.")
    parser.add_argument("prompt", nargs="?", default="", help="The prompt or policy request to evaluate.")
    parser.add_argument("--model", default="", help="Optional model name to include in the evaluation.")
    parser.add_argument("--risk-level", choices=["low", "medium", "high"], default="low", help="Declared risk level for the request.")
    parser.add_argument("--require-human-review", action="store_true", default=True, help="Require human review if issues are found.")
    parser.add_argument("--skip-human-review", dest="require_human_review", action="store_false", help="Skip the default requirement for human review.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.prompt:
        parser.print_help()
        return 0

    result = GovernancePolicy(require_human_review=args.require_human_review).evaluate(
        args.prompt,
        model=args.model,
        risk_level=args.risk_level,
    )

    if result.issues:
        print(f"Status: requires review ({result.risk_level} risk)")
        for issue in result.issues:
            print(f"- [{issue.severity}] {issue.category}: {issue.description}")
        if result.approved:
            print("Recommended action: proceed only after review approval.")
        else:
            print("Recommended action: block until human review approves the request.")
    else:
        print(f"Status: approved ({result.risk_level} risk)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
