from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import re
from typing import Callable

from .analyst import GroundedAnalyst
from .calculations import unavailable_track_indicators
from .models import ResearchReport, ResearchRequest
from .sources import EvidenceCollector
from .universe import TRACKS, companies_for_track

STAGE_NAMES = ["Planner", "Researcher", "Extractor", "Verifier", "Triangulator", "Analyst", "Skeptic", "Reporter"]


def plan_queries(request: ResearchRequest) -> tuple[list[str], list[tuple[str, str]]]:
    signals = TRACKS[request.track]["signals"]
    planned = [f"What do recent public disclosures say about {signal} for {request.company}?" for signal in signals]
    if request.question.strip():
        planned.insert(0, request.question.strip())
    period = f' {request.reporting_period}' if request.reporting_period else " latest reported period"
    queries = []
    for signal in signals:
        query = f'"{request.company}" {request.ticker} {signal}{period} results disclosure'.replace("  ", " ")
        queries.append((f"Signal · {signal}", query))
    queries.extend([
        ("Company / investor material · filings", f'"{request.company}" {request.ticker} annual report quarterly results investor presentation{period}'),
        ("Company / investor material · investor relations", f'"{request.company}" {request.ticker} investor relations earnings call transcript presentation{period}'),
        ("Exchange / regulatory · filings", f'"{request.company}" {request.ticker} site:nseindia.com OR site:bseindia.com filing results announcement{period}'),
        ("Public data · official sector sources", f'{request.sector or request.track} India site:gov.in OR site:nic.in regulator industry statistics report{period}'),
        ("Industry / competitor · peer comparison", f'"{request.company}" {request.sector or request.track} competitor peer results volume demand{period}'),
        ("Credible news · independent coverage", f'"{request.company}" {request.question} (site:business-standard.com OR site:economictimes.indiatimes.com OR site:moneycontrol.com){period}'),
    ])
    peer_entries = [item for item in companies_for_track(request.track) if item["company"].lower() != request.company.lower()][:2]
    for peer in peer_entries:
        queries.append((f"Industry / competitor · peer {peer['company']}",
                        f'"{request.company}" "{peer["company"]}" {request.sector or request.track} same period comparison{period}'))
    queries.extend([
        ("Counterevidence · adverse evidence", f'"{request.company}" {request.question} risk decline delay adverse missed target'),
        ("Counterevidence · alternative explanations", f'"{request.company}" {request.question} competitor industry one-off base effect alternative explanation'),
    ])
    return planned, queries


def _candidate_passages(evidence, request: ResearchRequest) -> list[dict]:
    """Surface verbatim, relevant paragraphs for review; these are not verified claims."""
    stopwords = {"about", "after", "against", "among", "could", "does", "from", "have", "into", "more", "than", "that", "their", "there", "these", "this", "through", "under", "what", "when", "which", "with", "would", "your", "company", "latest", "reported", "period"}
    candidates: dict[str, list[dict]] = defaultdict(list)
    for item in evidence:
        terms = {word for word in re.findall(r"[a-zA-Z]{3,}", item.signal_category.lower()) if word not in stopwords}
        if request.question:
            terms.update(word for word in re.findall(r"[a-zA-Z]{4,}", request.question.lower()) if word not in stopwords)
        paragraphs = item.relevant_passages or [part.strip() for part in re.split(r"(?<=[.!?])\s+", item.extracted_text) if len(part.strip()) > 50]
        ranked = []
        for index, passage in enumerate(paragraphs):
            lower = passage.lower()
            score = sum(1 for term in terms if term in lower)
            has_numeric = bool(re.search(r"(?:\d[\d,.]*\s?%|(?:INR|Rs\.?|₹)\s?[\d,.]+|\b\d{1,3}(?:,\d{3})+\b)", passage, re.IGNORECASE))
            if score >= 1 and len(passage) >= 70:
                ranked.append((score + (2 if has_numeric else 0), index, passage.strip()))
        for _, index, passage in sorted(ranked, reverse=True)[:2]:
            pdf_page = re.match(r"\[PDF page (\d+)\]", passage)
            locator = f"PDF page {pdf_page.group(1)}" if pdf_page else f"Extracted HTML paragraph {index + 1}"
            candidates[item.signal_category].append({
                "evidence_id": item.evidence_id, "title": item.source_title,
                "publisher": item.publisher, "url": item.original_url,
                "passage": passage[:1400], "locator": f"{locator}; confirm against original document",
                "publication_date": item.publication_date,
                "reporting_period_candidate": item.reporting_period_candidate,
                "source_type": item.source_type, "verification_status": item.verification_status,
            })
    return [
        {"signal": signal, "label": f"Review lead: retrieved passages mention {signal}",
         "status": "unverified_passage_candidates", "passages": passages[:6],
         "caution": "Keyword relevance is a navigation aid, not semantic verification that the passage supports a conclusion."}
        for signal, passages in candidates.items() if passages
    ]


def _timeline(evidence) -> list[dict]:
    items = []
    for item in evidence:
        if item.publication_date:
            items.append({"date": item.publication_date, "date_basis": item.date_basis,
                          "reporting_period_candidate": item.reporting_period_candidate,
                          "signal": item.signal_category, "title": item.source_title,
                          "publisher": item.publisher, "url": item.original_url,
                          "evidence_id": item.evidence_id,
                          "note": "Publication date metadata; not necessarily the period described by the source."})
    return sorted(items, key=lambda row: row["date"])


def _triangulate(evidence):
    domains: dict[str, list] = defaultdict(list)
    fingerprints: dict[str, list] = defaultdict(list)
    for item in evidence:
        domains[item.publisher].append(item)
        if item.content_fingerprint:
            fingerprints[item.content_fingerprint].append(item)
    repeated = [{"domains": sorted({e.publisher for e in group}), "urls": [e.original_url for e in group],
                "note": "Near-identical extracted page content: do not count these results as separate confirmation."}
               for group in fingerprints.values() if len(group) > 1]
    # Domain variety is a screening signal only; ownership, syndication and source derivation are not established.
    # Multiple domains alone do not establish semantic agreement or independence.
    corroborated = []
    periods = defaultdict(list)
    for item in evidence:
        if item.reporting_period_candidate:
            periods[item.reporting_period_candidate].append(item.original_url)
    mismatch = []
    if len(periods) > 1:
        mismatch.append({"type": "reporting_period_candidates", "periods": dict(periods),
                 "note": "Heuristically detected period candidates differ; confirm periods in the original documents before comparison."})
    contradiction = repeated + mismatch
    if evidence:
        contradiction.append({"type": "cross_source_verification_limit", "note": "No semantic claim-to-source or true source-independence test is automated; no corroboration is asserted."})
    return corroborated, contradiction


def _confidence(evidence, request: ResearchRequest) -> tuple[str, str]:
    fetched = [e for e in evidence if e.verification_status == "page_fetched" and len(e.extracted_text) > 120]
    primary = [e for e in fetched if e.source_type in ("primary_regulatory_or_exchange", "potential_company_primary")]
    domains = {e.publisher for e in fetched}
    reasons = [f"{len(evidence)} search results retained; {len(fetched)} pages yielded text; {len(primary)} are classified as potential primary/regulatory sources."]
    reasons.append(f"Evidence spans {len(domains)} domains, but domain difference does not prove source independence.")
    reasons.append("No claim-to-source semantic support review or structured financial-value verification is automated.")
    reasons.append("All automated classifications remain unverified; this run cannot qualify for Moderate or Strong evidence strength.")
    return "Weak", "Weak: retrieved coverage is not the same as validated evidence. " + " ".join(reasons)


class ResearchAgent:
    def __init__(self, collector: EvidenceCollector | None = None, analyst: GroundedAnalyst | None = None):
        self.collector = collector or EvidenceCollector()
        self.analyst = analyst or GroundedAnalyst()

    def run(self, request: ResearchRequest, per_query: int = 4,
            progress: Callable[[str, str], None] | None = None) -> ResearchReport:
        stages = []
        errors: list[str] = []

        def mark(name: str, status: str, detail: str):
            stages.append({"stage": name, "status": status, "detail": detail, "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds")})
            if progress:
                progress(name, detail)

        if request.track not in TRACKS:
            raise ValueError(f"Unknown research track: {request.track}")
        planned, queries = plan_queries(request)
        mark("Planner", "completed", f"Prepared {len(planned)} track-specific subquestions and {len(queries)} search queries.")
        mark("Researcher", "running", "Searching public web results; access and coverage depend on provider/network availability.")
        evidence, search_errors = self.collector.collect(request, queries, per_query=per_query,
                                                         progress=lambda stage, detail: progress(stage, detail) if progress else None)
        errors.extend(search_errors)
        mark("Researcher", "completed" if evidence else "incomplete", f"Collected {len(evidence)} unique URL results; {len(search_errors)} query errors.")
        extracted = sum(bool(e.extracted_text) for e in evidence)
        candidate_signals = _candidate_passages(evidence, request)
        timeline = _timeline(evidence)
        mark("Extractor", "completed", f"Extracted page text for {extracted}/{len(evidence)} results; surfaced {sum(len(signal['passages']) for signal in candidate_signals)} exact passage candidates.")
        verified = sum(e.verification_status == "page_fetched" for e in evidence)
        marks = sum(bool(e.relevant_passages) for e in evidence)
        mark("Verifier", "limited", f"Fetched {verified} pages; retained paragraph/page passages for {marks}; source-to-claim support, URL ownership and reporting periods still require human review.")
        groups, contradictions = _triangulate(evidence)
        mark("Triangulator", "completed", f"Checked exact-content duplication and detectable period mismatches; source independence is not asserted.")
        indicators = TRACKS[request.track]["indicators"]
        calculations = unavailable_track_indicators(request.track, indicators)
        analysis_draft = None
        try:
            analysis_draft = self.analyst.analyze(request, evidence)
            if analysis_draft:
                timeline.extend({**event,
                                 "reporting_period_candidate": event.get("period_as_reported") or None,
                                 "signal": "model-extracted event (review required)",
                                 "title": next((item.source_title for item in evidence if item.evidence_id == event["evidence_id"]), "Source event"),
                                 "publisher": next((item.publisher for item in evidence if item.evidence_id == event["evidence_id"]), "unknown"),
                                 "note": "Date and period were quote-matched; event meaning and dates require human review."}
                                for event in analysis_draft.get("timeline_events", []))
                timeline.sort(key=lambda item: item.get("date", ""))
                mark("Analyst", "draft_requires_review", "Optional model generated a draft; only exact source quotes survived validation. Human review remains mandatory.")
            else:
                mark("Analyst", "limited", "Grounded synthesis is disabled. No financial calculations made: no structured, verified numeric inputs were available.")
        except Exception as exc:
            errors.append(str(exc))
            mark("Analyst", "failed", f"Optional grounded analysis failed; retrieval evidence is retained without synthesizing claims: {exc}")
        mark("Skeptic", "completed", "Ran adverse/risk and competitor/alternative search queries; absence of results is not evidence of absence.")
        confidence, confidence_explanation = _confidence(evidence, request)
        domains = sorted({e.publisher for e in evidence})
        alternatives = [
            "The observed theme may reflect a sector-wide or macroeconomic driver rather than company-specific execution.",
            "A one-off base effect, accounting/presentation change, or reporting-period mismatch may explain apparent movement.",
            "Search and web-access gaps may omit material counterevidence; no conclusion can be drawn from missing results.",
        ]
        supported_count = len((analysis_draft or {}).get("supporting_claims", []))
        if not evidence:
            hypothesis = "Unverified: the available research run did not retrieve source evidence to assess the proposed hypothesis."
        elif supported_count and analysis_draft:
            hypothesis = f"DRAFT ONLY — {analysis_draft['discovery_draft']}"
        else:
            hypothesis = (f"No verified discovery can be responsibly reported yet. Review {len(candidate_signals)} signal category/ies with relevant passage candidates for {request.company}; "
                          "automated keyword matches do not establish that the passages support a conclusion.")
        mark("Reporter", "completed", "Generated a cautious report with traceable results, explicit unknowns, and a falsification test.")
        limitations = [
            "Search results are discovery leads. Search snippets alone are not treated as proof.",
            "A fetched page is not automatically evidence that the source supports a claim; review the linked source text.",
            "Publication dates come from page metadata when available. Reporting-period strings are heuristic candidates and must be confirmed in source documents.",
            "Syndication can evade exact-content deduplication. Different domains are not assumed to be independent.",
            "No LLM-generated financial facts are used. Number-like passages are surfaced verbatim for review; they are not parsed or used in calculations.",
            f"Domains observed in this run: {', '.join(domains) if domains else 'none'}.",
        ]
        if request.reporting_period:
            limitations.append(f"Requested reporting period: {request.reporting_period}. Verify that each source covers this period.")
        limitations.extend(errors)
        return ResearchReport(
            request=request, created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"), stages=stages,
            planned_questions=planned, evidence=evidence, calculations=calculations,
            corroborated_groups=groups, contradictions=contradictions, alternatives=alternatives,
            hypothesis=hypothesis, why_it_matters="If verified, the signal may change how durable the company's growth, risk, or operating trajectory is assessed. No valuation or investment conclusion follows.",
            falsification_condition="The hypothesis is weakened or falsified if primary disclosures for the requested comparable periods show no relevant change, show the opposite direction, or establish a documented one-off/sector-wide explanation.",
            next_steps=["Open and review each cited filing or company disclosure; confirm period, units, and claim context.", "Obtain comparable reported values for at least two periods and enter them in the cited calculation panel.", "Search a peer and a regulator/official source for the same period; trace any repeated press-release origin.", "Re-run the research after counterevidence is reviewed and update the evidence set."],
            confidence=confidence, confidence_explanation=confidence_explanation,
            limitations=limitations, pipeline_errors=errors, timeline=timeline,
            candidate_signals=candidate_signals,
            why_it_matters_bullets=[
                "If confirmed in primary filings, this signal could change the assessment of operating momentum or risk.",
                "Checking comparable periods can distinguish a persistent shift from a one-off event or base effect.",
                "Peer and sector evidence is needed to decide whether a pattern is company-specific or industry-wide.",
            ],
            discovery_status=("llm_draft_requires_human_review" if supported_count else "unverified_research_leads") if evidence else "no_evidence_retrieved",
            analysis_draft=analysis_draft,
        )
