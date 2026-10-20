from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class ResearchRequest:
    company: str
    track: str
    question: str
    ticker: str = ""
    exchange: str = "NSE"
    sector: str = ""
    reporting_period: str = ""


@dataclass
class Evidence:
    company: str
    track: str
    signal_category: str
    source_title: str
    publisher: str
    original_url: str
    snippet: str
    search_query: str
    source_type: str
    retrieval_timestamp: str = field(default_factory=utc_now)
    evidence_id: str = field(default_factory=lambda: str(uuid4()))
    publication_date: str | None = None
    reporting_period: str | None = None
    extracted_text: str = ""
    numeric_value: float | None = None
    numeric_unit: str | None = None
    verification_status: str = "search_result_unverified"
    limitations: list[str] = field(default_factory=list)
    content_fingerprint: str = ""
    source_group: str = "other"
    date_basis: str = "unavailable"
    reporting_period_candidate: str | None = None
    relevant_passages: list[str] = field(default_factory=list)
    passage_locator: str = ""
    tone_hints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Calculation:
    name: str
    status: str
    formula: str
    value: float | None
    unit: str
    inputs: dict[str, Any]
    periods: dict[str, str]
    source_urls: list[str]
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ResearchReport:
    request: ResearchRequest
    created_at: str
    stages: list[dict[str, Any]]
    planned_questions: list[str]
    evidence: list[Evidence]
    calculations: list[Calculation]
    corroborated_groups: list[list[str]]
    contradictions: list[dict[str, Any]]
    alternatives: list[str]
    hypothesis: str
    why_it_matters: str
    falsification_condition: str
    next_steps: list[str]
    confidence: str
    confidence_explanation: str
    limitations: list[str]
    pipeline_errors: list[str]
    timeline: list[dict[str, Any]] = field(default_factory=list)
    candidate_signals: list[dict[str, Any]] = field(default_factory=list)
    why_it_matters_bullets: list[str] = field(default_factory=list)
    discovery_status: str = "unverified_research_leads"
    analysis_draft: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "request": asdict(self.request), "created_at": self.created_at,
            "stages": self.stages, "planned_questions": self.planned_questions,
            "evidence": [item.to_dict() for item in self.evidence],
            "calculations": [item.to_dict() for item in self.calculations],
            "corroborated_groups": self.corroborated_groups,
            "contradictions": self.contradictions, "alternatives": self.alternatives,
            "hypothesis": self.hypothesis, "why_it_matters": self.why_it_matters,
            "falsification_condition": self.falsification_condition,
            "next_steps": self.next_steps, "confidence": self.confidence,
            "confidence_explanation": self.confidence_explanation,
            "limitations": self.limitations, "pipeline_errors": self.pipeline_errors,
            "timeline": self.timeline, "candidate_signals": self.candidate_signals,
            "why_it_matters_bullets": self.why_it_matters_bullets,
            "discovery_status": self.discovery_status,
            "analysis_draft": self.analysis_draft,
        }
