from __future__ import annotations

import json
import html
import os
import re
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from signaltrace.analyst import GroundedAnalyst
from signaltrace.calculations import inventory_growth, receivables_growth, revenue_growth, reviewed_observation_growth
from signaltrace.models import ResearchRequest
from signaltrace.pipeline import ResearchAgent
from signaltrace.universe import NIFTY50, TRACKS, companies_for_track

load_dotenv()

st.set_page_config(page_title="SignalTrace AI | Research terminal", page_icon="⌁", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
:root{--ink:#e9f1ff;--muted:#91a5bf;--cyan:#51e0dc;--blue:#668cff;--violet:#a68bff;--panel:#0d1728;--stroke:rgba(151,181,223,.15)}
[data-testid="stAppViewContainer"]{color:var(--ink);font-family:'Manrope',sans-serif}
[data-testid="stAppViewContainer"]{background:radial-gradient(ellipse at 78% 2%,rgba(44,81,145,.27),transparent 32%),radial-gradient(ellipse at 3% 38%,rgba(28,108,111,.12),transparent 30%),#070c16}
[data-testid="stHeader"]{background:rgba(7,12,22,.72);backdrop-filter:blur(14px)}
.block-container{max-width:1440px;padding-top:1.5rem;padding-bottom:5rem}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0b1322,#080e19 75%);border-right:1px solid rgba(120,153,197,.14)}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p{color:#9aacc5}
[data-testid="stSidebar"] [role="radiogroup"] label{padding:9px 12px;border-radius:10px;transition:all .18s ease}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:#121e32}
.trace-hero{position:relative;overflow:hidden;padding:31px 36px;border:1px solid rgba(127,177,226,.2);border-radius:23px;background:linear-gradient(112deg,rgba(17,31,52,.98) 0%,rgba(14,26,46,.95) 56%,rgba(25,31,65,.94) 100%);box-shadow:0 22px 70px rgba(0,0,0,.22);margin:8px 0 24px}
.trace-hero:after{content:"";position:absolute;width:380px;height:380px;right:-110px;top:-190px;border-radius:50%;background:radial-gradient(circle,rgba(80,220,218,.19),rgba(117,105,255,.09) 42%,transparent 70%);pointer-events:none}
.trace-kicker{font:600 10px 'DM Mono',monospace;letter-spacing:.22em;text-transform:uppercase;color:#67e3dd}
.trace-hero-title{font:800 clamp(30px,4vw,51px)/1.04 'Manrope',sans-serif;letter-spacing:-.055em;color:#f1f6ff;margin:14px 0 11px;max-width:800px}
.trace-hero-copy{max-width:670px;color:#a3b4cb;font-size:14px;line-height:1.75;margin:0}
.trace-meta{display:inline-block;margin-top:9px;color:#8095b1;font:11px 'DM Mono',monospace;letter-spacing:.02em}
.trace-pills{display:flex;gap:8px;flex-wrap:wrap;margin-top:21px}
.trace-pill{font:500 10px 'DM Mono',monospace;color:#c7d6eb;background:rgba(126,161,210,.08);border:1px solid rgba(147,180,224,.16);padding:7px 10px;border-radius:99px}
.trace-card{position:relative;overflow:hidden;background:linear-gradient(150deg,rgba(19,32,52,.96),rgba(10,18,31,.98));border:1px solid rgba(135,171,218,.16);border-radius:16px;padding:18px 20px;min-height:108px;box-shadow:0 8px 25px rgba(0,0,0,.12);transition:transform .18s,border-color .18s}
.trace-card:hover{transform:translateY(-2px);border-color:rgba(81,224,220,.35)}
.trace-card-label{color:#8ea4c0;font:600 10px 'DM Mono',monospace;text-transform:uppercase;letter-spacing:.13em}
.trace-card-value{color:#f3f7ff;font-size:26px;font-weight:800;letter-spacing:-.045em;margin-top:9px}
.trace-card-note{color:#8196b1;font-size:11px;line-height:1.5;margin-top:4px}
section[data-testid="stForm"]{background:linear-gradient(145deg,rgba(14,25,42,.98),rgba(10,17,30,.98));border:1px solid rgba(135,171,218,.2);border-radius:18px;padding:22px 24px;box-shadow:0 16px 45px rgba(0,0,0,.17)}
div[data-baseweb="input"]>div,div[data-baseweb="textarea"]>div,div[data-baseweb="select"]>div{background:#0b1422;border-color:#273850;border-radius:10px}
div[data-baseweb="input"]:focus-within>div,div[data-baseweb="textarea"]:focus-within>div{border-color:#51d9d5;box-shadow:0 0 0 1px #51d9d5}
.stButton>button[kind="primary"]{background:linear-gradient(105deg,#48dcd5 0%,#8ab5ff 55%,#a48cff 100%);border:0;color:#08111e;font-weight:800;border-radius:11px;padding:.72rem 1.1rem;box-shadow:0 7px 22px rgba(73,203,214,.17);transition:filter .2s,transform .2s}
.stButton>button[kind="primary"]:hover{filter:brightness(1.08);transform:translateY(-1px)}
.stButton>button{border-radius:10px;border-color:#2c405b;transition:all .2s}
[data-testid="stMetric"]{background:linear-gradient(150deg,#111e31,#0b1421);padding:16px 18px;border:1px solid rgba(135,171,218,.16);border-radius:14px}
[data-testid="stExpander"],div[data-testid="stTabs"] button{border-color:rgba(135,171,218,.17);border-radius:11px}
[data-testid="stTabs"] [role="tablist"]{gap:7px;border-bottom:1px solid rgba(135,171,218,.15)}
[data-testid="stTabs"] button[aria-selected="true"]{color:#65e2dd;border-bottom-color:#55deda}
[data-testid="stDataFrame"]{border:1px solid rgba(135,171,218,.17);border-radius:13px;overflow:hidden}
.stCaption,small{color:#8da1bb!important}
hr{border-color:rgba(135,171,218,.14)}
a{color:#71e2df!important}
div[data-testid="stAlert"]{border-radius:13px;border:1px solid rgba(135,171,218,.15)}
@media(max-width:760px){.trace-hero{padding:24px 20px;border-radius:17px}.trace-hero-title{font-size:34px}.block-container{padding-left:1rem;padding-right:1rem}}
</style>
""", unsafe_allow_html=True)

if "report" not in st.session_state:
    st.session_state.report = None
if "batch_reports" not in st.session_state:
    st.session_state.batch_reports = []


def card(label: str, value: str, note: str = "") -> str:
    return f'<div class="trace-card"><div class="trace-card-label">{label}</div><div class="trace-card-value">{value}</div><div class="trace-card-note">{note}</div></div>'


def source_type_label(value: str) -> str:
    return {"primary_regulatory_or_exchange": "Official exchange / regulator candidate", "public_sector_or_regulatory": "Public-sector source candidate", "potential_company_primary": "Potential company source", "secondary_or_unclassified": "Secondary / unclassified"}.get(value, value)


def reviewed_evidence_strength(report) -> tuple[str, str]:
    """Only raise Weak after explicit quote review and a human source-independence attestation."""
    draft = report.analysis_draft or {}
    support = draft.get("supporting_claims", [])
    all_claims = support + draft.get("contradictory_claims", [])
    citations = [citation for claim in all_claims for citation in claim.get("citations", [])]
    domains = {citation.get("domain") for citation in citations if citation.get("domain")}
    if not support or not citations:
        return "Weak", "No multi-source supporting claim survived exact-quote checks; source-backed discovery remains unverified."
    all_quotes_checked = True
    for claim_index, claim in enumerate(all_claims):
        bucket = "supporting_claims" if claim_index < len(support) else "contradictory_claims"
        support_index = claim_index if bucket == "supporting_claims" else claim_index - len(support)
        for citation_index, citation in enumerate(claim.get("citations", [])):
            key = f"review_{bucket}_{support_index}_{citation['evidence_id']}_{citation_index}"
            all_quotes_checked = all_quotes_checked and bool(st.session_state.get(key, False))
    independence_confirmed = bool(st.session_state.get(f"independence_{report.created_at}", False))
    distinct_sources = len({(citation.get("domain"), citation.get("source_group")) for citation in citations})
    primary_domains = {citation.get("domain") for citation in citations
                       if citation.get("source_type_candidate") == "primary_regulatory_or_exchange"}
    if all_quotes_checked and independence_confirmed and len(domains) >= 3 and len(primary_domains) >= 2 and distinct_sources >= 3:
        return "Strong", "Human review confirmed every cited passage and attested to independent source origins; at least three domains, two potential official/regulatory domains, and three source groups are present. Automated interpretation remains fallible."
    if all_quotes_checked and independence_confirmed and len(domains) >= 2 and distinct_sources >= 2:
        return "Moderate", "Human review confirmed every cited passage and attested to independence; at least two domains and source groups are present. Source completeness and interpretation still require judgment."
    return "Weak", "Weak until all claim passages are reviewed and the cited origins are independently checked. Domain diversity alone does not prove independence."


def render_report(report):
    if report is None:
        st.markdown('<div class="trace-eyebrow">Research workspace</div><h2>Start with a question, not a ticker.</h2><p class="trace-sub">SignalTrace gathers public research leads, preserves provenance, and makes uncertainty visible. It does not provide investment advice.</p>', unsafe_allow_html=True)
        return
    req = report.request
    display_confidence, display_confidence_explanation = reviewed_evidence_strength(report)
    st.markdown(f'<section class="trace-hero"><div class="trace-kicker">{html.escape(req.track)} · {html.escape(req.exchange)} {html.escape(req.ticker or "Ticker not supplied")}</div><div class="trace-hero-title">{html.escape(req.company)}</div><p class="trace-hero-copy">{html.escape(req.question or "Track-level signal scan")}<br><span class="trace-meta">Run {html.escape(report.created_at)} · {html.escape(report.discovery_status.replace("_", " ").title())}</span></p></section>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    fetched = sum(e.verification_status == "page_fetched" for e in report.evidence)
    reviewed_calc_key = f"reviewed_calculations_{report.created_at}"
    calculated_count = sum(c.status == "calculated" for c in report.calculations) + sum(
        item.get("status") == "calculated" for item in st.session_state.get(reviewed_calc_key, [])
    )
    m1.markdown(card("Evidence strength", display_confidence, "Requires human source review"), unsafe_allow_html=True)
    m2.markdown(card("Evidence leads", str(len(report.evidence)), "Unique URLs after deduplication"), unsafe_allow_html=True)
    m3.markdown(card("Pages with text", str(fetched), "Retrieval does not verify claim support"), unsafe_allow_html=True)
    m4.markdown(card("Calculations", str(calculated_count), "Includes only cited, comparable reviewed inputs"), unsafe_allow_html=True)

    st.markdown("### Discovery desk")
    st.markdown(f"**Status · {report.discovery_status.replace('_', ' ').title()}**")
    if report.analysis_draft and report.analysis_draft.get("supporting_claims"):
        discovery_text = report.analysis_draft.get("discovery_draft", report.hypothesis)
        discovery_label = "Human-reviewed draft discovery" if display_confidence in {"Moderate", "Strong"} else "Draft discovery · review required"
    else:
        discovery_text = report.hypothesis
        discovery_label = "Research hypothesis / status"
    st.info(f"**{discovery_label}:** {discovery_text}")
    why_col, falsify_col = st.columns([1, 1])
    with why_col:
        st.markdown("**Why this could matter**")
        for item in ((report.analysis_draft or {}).get("why_it_matters") or report.why_it_matters_bullets):
            st.markdown(f"- {item}")
    with falsify_col:
        st.markdown("**Falsification condition**")
        st.write((report.analysis_draft or {}).get("falsification_condition") or report.falsification_condition)
        st.markdown("**Evidence strength · " + display_confidence + "**")
        st.caption(display_confidence_explanation)

    if report.candidate_signals:
        st.markdown("#### Passage leads · analyst review required")
        st.caption("These are verbatim text matches surfaced for navigation. They are not findings, verified facts, or corroboration.")
        for candidate in report.candidate_signals:
            with st.expander(f"{candidate['signal']} · {len(candidate['passages'])} passage lead(s)"):
                st.caption(candidate["caution"])
                for passage in candidate["passages"]:
                    st.markdown(f"**[{passage['title']}]({passage['url']})** · {passage['publisher']} · {passage['verification_status']}")
                    st.code(passage["passage"], language=None)
                    st.caption(f"{passage['locator']} · publication date: {passage['publication_date'] or 'not extracted'} · period candidate: {passage['reporting_period_candidate'] or 'not extracted'}")

    if report.analysis_draft:
        draft = report.analysis_draft
        st.markdown("#### Grounded model draft · review before use")
        st.warning("The model saw only retrieved excerpts. Exact quotation matching checks that cited text exists; it does not prove the interpretation is correct. Verify every passage and numeric item in the original document.")
        st.markdown("**Draft discovery:** " + draft.get("discovery_draft", "Not supplied"))
        st.markdown("**Draft temporal interpretation:** " + draft.get("temporal_summary", "Not established"))
        for bucket, heading in (("supporting_claims", "Supporting claim drafts"), ("contradictory_claims", "Contradictory evidence drafts")):
            claims = draft.get(bucket, [])
            st.markdown(f"**{heading} ({len(claims)})**")
            if not claims:
                st.caption("No quote-validated claim drafts in this category.")
            for claim_index, claim in enumerate(claims):
                st.markdown(f"- {claim['claim']}")
                for citation_index, citation in enumerate(claim.get("citations", [])):
                    st.markdown(f"  - [{citation['domain']} source]({citation['url']}) · “{citation['quote']}”")
                    review_id = f"review_{bucket}_{claim_index}_{citation['evidence_id']}_{citation_index}"
                    st.checkbox("I opened the original source and confirmed this quote supports the claim", key=review_id)
        if draft.get("supporting_claims"):
            st.checkbox("I checked that the cited publications are genuinely independent (not syndicated copies or the same originating release)", key=f"independence_{report.created_at}")
            new_strength, new_strength_reason = reviewed_evidence_strength(report)
            st.info(f"Current reviewed evidence strength: **{new_strength}** — {new_strength_reason}")
        observations = draft.get("numeric_observations", [])
        st.markdown(f"**Number-like observations ({len(observations)})**")
        if observations:
            st.dataframe(pd.DataFrame([{k: item.get(k, "") for k in ("metric", "value_as_reported", "unit_as_reported", "period_as_reported", "quote", "url", "review_status")} for item in observations]), width="stretch", hide_index=True,
                         column_config={"url": st.column_config.LinkColumn("Source URL", display_text="Open source")})
            for index, item in enumerate(observations):
                st.checkbox("I checked this value, unit and reporting period against the original source", key=f"review_number_{index}_{item['evidence_id']}")
        st.markdown("**Strongest alternative explanations**")
        for item in draft.get("alternative_explanations", []):
            st.markdown(f"- {item}")
        st.markdown("**Draft falsification condition:** " + draft.get("falsification_condition", "Not supplied"))
        st.markdown("**Next tests**")
        for item in draft.get("next_steps", []):
            st.markdown(f"- {item}")

    left, right = st.columns([1.15, .85])
    with left:
        st.markdown("### Evidence map")
        if report.evidence:
            counts = pd.DataFrame([{"Signal": e.signal_category, "Research layer": e.source_group, "Page text": "Extracted" if e.extracted_text else "Unavailable"} for e in report.evidence])
            fig = px.bar(counts.groupby(["Signal", "Research layer"], as_index=False).size(), x="Signal", y="size", color="Research layer", barmode="stack", color_discrete_sequence=["#51e0dc", "#a68bff", "#86aaff", "#ffbd72", "#f18cb7", "#7c91ad"])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#d8e6f5", margin=dict(l=0,r=0,t=10,b=0), xaxis_title="", yaxis_title="Search results", legend_title="", height=300)
            fig.update_xaxes(gridcolor="#203248", tickangle=-25)
            fig.update_yaxes(gridcolor="#203248")
            st.plotly_chart(fig, width="stretch")
        else:
            st.warning("No search results were obtained. Check network access and retry; no findings have been inferred.")
    with right:
        st.markdown("### What could change the view")
        draft_analysis = report.analysis_draft or {}
        for claim in draft_analysis.get("contradictory_claims", []):
            st.markdown(f"- **Counterevidence lead:** {claim['claim']}")
            for citation in claim.get("citations", []):
                st.markdown(f"  - [{citation['domain']} source]({citation['url']}) · “{citation['quote']}”")
        alternatives = draft_analysis.get("alternative_explanations") or report.alternatives
        for text in alternatives:
            st.markdown(f"- {text}")
        st.markdown("### Next tests")
        for text in report.next_steps:
            st.markdown(f"- {text}")

    st.markdown("### Research timeline")
    if report.timeline:
        timeline_df = pd.DataFrame(report.timeline)
        timeline_df["date"] = pd.to_datetime(timeline_df["date"], errors="coerce")
        timeline_df = timeline_df.dropna(subset=["date"])
        if not timeline_df.empty:
            fig = px.scatter(timeline_df, x="date", y="signal", color="publisher", hover_name="title",
                             hover_data={"reporting_period_candidate": True, "date_basis": True, "url": True},
                             color_discrete_sequence=["#59e2dc", "#a98eff", "#86aaff", "#ffbd72", "#f18cb7"])
            fig.update_traces(marker=dict(size=13, line=dict(width=1, color="#e6f4ff")))
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#d8e6f5",
                              margin=dict(l=0,r=0,t=12,b=0), height=330, xaxis_title="Publication date", yaxis_title="Signal category", legend_title="Publisher")
            fig.update_xaxes(gridcolor="#203248")
            fig.update_yaxes(gridcolor="#203248", categoryorder="category ascending")
            st.plotly_chart(fig, width="stretch")
            st.caption("Timeline uses publication-date metadata. It does not imply when the reported financial change occurred.")
            timeline_rows = []
            for event in report.timeline:
                timeline_rows.append({
                    "Date": event.get("date", ""), "Date basis": event.get("date_basis", ""),
                    "Reporting period (candidate)": event.get("reporting_period_candidate") or "Not stated",
                    "Event / signal": event.get("event") or event.get("signal", ""),
                    "Source": event.get("title", ""), "Evidence quote": event.get("quote", ""),
                    "URL": event.get("url", ""), "Review status": event.get("review_status", "source publication metadata"),
                })
            st.dataframe(pd.DataFrame(timeline_rows), width="stretch", hide_index=True,
                         column_config={"URL": st.column_config.LinkColumn("Source", display_text="Open source")})
        else:
            st.info("Dates were present but could not be normalized into timeline points.")
    else:
        st.info("No publication dates were reliably extracted. A timeline cannot be established from this run.")

    st.markdown("### Evidence register")
    st.caption("Search snippets are leads only. Open source pages to verify claim, period, unit, and context. A fetched page is not automatically a verified claim.")
    if report.evidence:
        rows = []
        for e in report.evidence:
            rows.append({"Search group":e.source_group, "Signal":e.signal_category, "Title":e.source_title, "Publisher/domain":e.publisher, "Source class":source_type_label(e.source_type), "Publication date":e.publication_date or "Not extracted", "Date source":e.date_basis, "Period candidate":e.reporting_period_candidate or "Not extracted", "Retrieval status":e.verification_status, "URL":e.original_url})
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True, column_config={"URL":st.column_config.LinkColumn("Source URL", display_text="Open source")})
        with st.expander("Inspect extracted source text and limitations"):
            for e in report.evidence:
                st.markdown(f"**{e.source_title}** · {e.publisher} · [{e.original_url}]({e.original_url})")
                st.caption(f"{e.source_group} · {e.signal_category} | {e.verification_status} | Published: {e.publication_date or 'unknown'} ({e.date_basis}) | Candidate data period: {e.reporting_period_candidate or 'unknown'}")
                if e.extracted_text:
                    st.write(e.extracted_text[:2400] + ("…" if len(e.extracted_text)>2400 else ""))
                else:
                    st.warning("Page content unavailable. Search snippet below is not proof.")
                if e.snippet:
                    st.caption("Search snippet: " + e.snippet)
                for limitation in e.limitations:
                    st.caption("Limitation: " + limitation)
                st.divider()
    else:
        st.info("No evidence items to display.")

    st.markdown("### Calculations and unresolved indicators")
    st.caption("Calculations are unavailable unless the inputs are comparable, manually checked against cited source pages, and entered in Calculator.")
    st.dataframe(pd.DataFrame([{"Indicator":c.name,"Status":c.status,"Formula":c.formula,"Value":c.value,"Unit":c.unit,"Note":c.note} for c in report.calculations]), width="stretch", hide_index=True)
    if report.contradictions:
        st.markdown("### Contradictions and warnings")
        for item in report.contradictions:
            st.warning(f"**{item.get('type','Deduplication warning')}:** {item.get('note','')} {item.get('periods','')}")
    else:
        st.markdown("### Contradictions and warnings")
        st.caption("No machine-detectable duplicate/period warning was found. This does not establish that evidence agrees.")
    st.markdown("### Workflow trace")
    st.dataframe(pd.DataFrame(report.stages), width="stretch", hide_index=True)
    st.markdown("### Limitations")
    for item in report.limitations:
        st.markdown(f"- {item}")

    base = re.sub(r"[^a-z0-9-]+", "-", req.company.lower()).strip("-") or "company"
    report_dict = report.to_dict()
    report_dict["confidence"] = display_confidence
    report_dict["confidence_explanation"] = display_confidence_explanation
    report_dict["human_review_checks"] = {key: bool(value) for key, value in st.session_state.items() if key.startswith(("review_", "independence_"))}
    report_dict["reviewed_calculations"] = st.session_state.get(f"reviewed_calculations_{report.created_at}", [])
    st.download_button("Download reproducible JSON", json.dumps(report_dict, indent=2, ensure_ascii=False), file_name=f"signaltrace-{base}.json", mime="application/json")
    if report.evidence:
        st.download_button("Export evidence CSV", pd.DataFrame([e.to_dict() for e in report.evidence]).to_csv(index=False), file_name=f"signaltrace-{base}-evidence.csv", mime="text/csv")


def build_request(company: str, track: str, question: str, ticker: str, exchange: str, sector: str, period: str) -> ResearchRequest:
    return ResearchRequest(company=company.strip(), track=track, question=question.strip(), ticker=ticker.strip(), exchange=exchange, sector=sector.strip(), reporting_period=period.strip())


with st.sidebar:
    st.markdown('<div class="trace-kicker">◈ SIGNALTRACE AI</div>', unsafe_allow_html=True)
    st.markdown("## Research studio")
    st.caption("PUBLIC-MARKET INTELLIGENCE · BETA")
    page = st.radio("Workspace", ["Research", "Track coverage", "Calculator", "Method & safeguards"], label_visibility="collapsed")
    st.divider()
    st.markdown("**Research controls**")
    model_default = os.getenv("SIGNALTRACE_ENABLE_LLM", "false").lower() in {"1", "true", "yes"}
    use_grounded_model = st.toggle("Grounded model draft", value=model_default,
                                   help="Optional OpenAI-compatible API. Source excerpts are sent to your configured provider. API key must be set in .env.")
    st.session_state["use_grounded_model"] = use_grounded_model
    if use_grounded_model and not os.getenv("SIGNALTRACE_LLM_API_KEY"):
        st.caption("Set SIGNALTRACE_LLM_API_KEY in .env to enable model analysis.")
    st.caption("Evidence-first · source-linked · falsifiable")
    st.caption("Research only. Not investment advice.")

if page == "Research":
    st.markdown('''<section class="trace-hero"><div class="trace-kicker">AUTONOMOUS FINANCIAL RESEARCH · ATMOS 2026</div><div class="trace-hero-title">See the signal<br>between the lines.</div><p class="trace-hero-copy">Trace a company question across public disclosures, industry context and counterevidence. Inspect the exact passages. Keep uncertainty visible.</p><div class="trace-pills"><span class="trace-pill">01 · DISCOVER</span><span class="trace-pill">02 · CONNECT</span><span class="trace-pill">03 · CHALLENGE</span><span class="trace-pill">04 · TRACE</span></div></section>''', unsafe_allow_html=True)
    with st.form("research_form"):
        track = st.selectbox("Hackathon research track", list(TRACKS.keys()))
        eligible_companies = companies_for_track(track)
        company_options = [str(item["company"]) for item in eligible_companies] + ["Other listed company · enter manually"]
        selected_company = st.selectbox("Company in selected track", company_options, help="Pick a configured NIFTY 50 company or test another listed company in the sector.")
        selected_entry = next((item for item in eligible_companies if item["company"] == selected_company), None)
        c1, c2, c3 = st.columns([1.5, 1, 1])
        if selected_company == "Other listed company · enter manually":
            company = c1.text_input("Company name", placeholder="e.g. listed sector peer")
        else:
            company = c1.text_input("Company name", value=selected_company, disabled=True)
        ticker = c2.text_input("Ticker (optional)", value=str(selected_entry["ticker"]) if selected_entry else "", placeholder="NSE symbol")
        exchange = c3.selectbox("Exchange", ["NSE", "BSE", "Other / unknown"])
        c4, c5 = st.columns(2)
        sector = c4.text_input("Sector", value=str(selected_entry["sector"]) if selected_entry else "", placeholder="Banking / power / FMCG")
        period = c5.text_input("Reporting period (optional)", placeholder="FY2025 or Q3 FY2026")
        question = st.text_area("Research question", placeholder="Is loan growth outpacing deposit growth, and what evidence could disprove that signal?", height=90)
        per_query = st.slider("Results per research angle", 1, 4, 2, help="More results increase network use. Access and coverage depend on public search availability.")
        submitted = st.form_submit_button("✦  Launch research run", type="primary", width="stretch")
    st.caption("A retrieved source is not a verified claim. Stronger-than-Weak evidence requires source and passage review.")
    if submitted:
        if not company.strip():
            st.error("Enter a company name to begin.")
        else:
            req = build_request(company, track, question, ticker, exchange, sector, period)
            progress = st.progress(0, text="Starting research workflow…")
            status_line = st.empty()
            stage_order = ["Planner", "Researcher", "Extractor", "Verifier", "Triangulator", "Analyst", "Skeptic", "Reporter"]
            completed = set()
            def update_progress(stage, detail):
                completed.add(stage)
                match = re.search(r"query (\d+)/(\d+)", detail)
                if stage == "Researcher" and match:
                    fraction = .12 + .48 * (int(match.group(1)) / max(int(match.group(2)), 1))
                else:
                    fraction = min(len(completed)/len(stage_order), 1.0)
                progress.progress(fraction, text=f"{stage}: {detail[:100]}")
                status_line.caption(f"Workflow stage: {stage}")
            try:
                st.session_state.report = ResearchAgent(analyst=GroundedAnalyst(enabled=use_grounded_model)).run(req, per_query=per_query, progress=update_progress)
            except Exception as exc:
                st.error(f"Research could not complete: {type(exc).__name__}: {exc}")
            finally:
                progress.empty()
    render_report(st.session_state.report)

elif page == "Track coverage":
    st.markdown('<div class="trace-eyebrow">Configurable starter universe · not live constituent data</div>', unsafe_allow_html=True)
    st.title("Track coverage")
    st.warning("The included NIFTY 50 names and track mappings are an editable starter list, not a live index feed. Confirm current constituents and classifications. Results are only counted after each selected run completes.")
    coverage_track = st.selectbox("Select a research track", list(TRACKS.keys()), key="coverage_track")
    eligible = companies_for_track(coverage_track)
    st.markdown(f"**Eligible companies in the configured starter mapping:** {len(eligible)}")
    if eligible:
        st.dataframe(pd.DataFrame(eligible), width="stretch", hide_index=True)
        names = [item["company"] for item in eligible]
        selected = st.multiselect("Companies to actually research (maximum 10 per batch)", names, default=names[:1])
        batch_question = st.text_input("Shared research question", "What company-specific risks and growth signals are visible in recent disclosures?")
        batch_period = st.text_input("Reporting period (optional)", key="batch_period", placeholder="FY2025")
        if st.button("Run selected company research", type="primary", disabled=not selected):
            if len(selected) > 10:
                st.error("Choose at most 10 companies per batch to limit requests.")
            else:
                st.session_state.batch_reports = []
                bar = st.progress(0, text="Preparing selected company coverage…")
                for index, name in enumerate(selected):
                    entry = next(item for item in eligible if item["company"] == name)
                    req = build_request(name, coverage_track, batch_question, str(entry["ticker"]), str(entry["exchange"]), str(entry["sector"]), batch_period)
                    try:
                        report = ResearchAgent(analyst=GroundedAnalyst(enabled=st.session_state.get("use_grounded_model", False))).run(req, per_query=2)
                        st.session_state.batch_reports.append(report)
                    except Exception as exc:
                        st.session_state.batch_reports.append({"company":name,"error":f"{type(exc).__name__}: {exc}"})
                    bar.progress((index+1)/len(selected), text=f"Completed research attempt for {name}")
                bar.empty()
                st.success(f"Completed {len(st.session_state.batch_reports)} attempt(s). A run with zero retrieved sources is not a successful evidence analysis.")
    if st.session_state.batch_reports:
        rows = []
        for item in st.session_state.batch_reports:
            if isinstance(item, dict):
                rows.append({"Company":item["company"],"Status":"Failed", "Evidence leads":0,"Confidence":"—","Error":item["error"]})
            else:
                rows.append({"Company":item.request.company,"Status":"Evidence retrieved" if item.evidence else "No evidence retrieved", "Evidence leads":len(item.evidence),"Confidence":item.confidence,"Error":""})
        st.markdown("### Actual run coverage")
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        st.download_button("Download batch manifest", json.dumps([x.to_dict() if not isinstance(x,dict) else x for x in st.session_state.batch_reports], indent=2), file_name="signaltrace-batch.json", mime="application/json")

elif page == "Calculator":
    st.markdown('<div class="trace-eyebrow">Source-cited inputs · no hidden assumptions</div>', unsafe_allow_html=True)
    st.title("Financial calculator")
    st.warning("Only enter comparable values copied from source pages you have reviewed. Inputs and URLs are user-supplied and are not independently verified here. Never infer volume growth from revenue.")
    metric = st.selectbox("Metric", ["Revenue growth", "Receivables growth", "Inventory growth"])
    with st.form("calc_form"):
        c1,c2=st.columns(2)
        current=c1.number_input("Current reported value", min_value=0.0, value=0.0, format="%.4f")
        previous=c2.number_input("Previous reported value", min_value=0.0, value=0.0, format="%.4f")
        unit=st.text_input("Unit (e.g. INR crore)", "INR crore")
        c3,c4=st.columns(2)
        current_period=c3.text_input("Current reporting period", placeholder="FY2025")
        previous_period=c4.text_input("Previous comparable period", placeholder="FY2024")
        c5,c6=st.columns(2)
        current_url=c5.text_input("Current value source URL")
        previous_url=c6.text_input("Previous value source URL")
        calc_submit=st.form_submit_button("Calculate", type="primary")
    if calc_submit:
        fn={"Revenue growth":revenue_growth,"Receivables growth":receivables_growth,"Inventory growth":inventory_growth}[metric]
        result=fn(current,previous,current_period,previous_period,current_url,previous_url)
        if result.status == "calculated":
            st.success(f"{metric}: **{result.value:.2f}%**")
            st.caption(f"Formula: {result.formula} · Inputs: {current:g} {unit} ({current_period}) and {previous:g} {unit} ({previous_period})")
            st.caption("Check that both periods are comparable and both source pages substantiate the values before using this result.")
        else:
            st.error("Calculation unavailable: " + result.note)
        st.json(result.to_dict())
    st.markdown("#### Track-specific indicator checklist")
    calc_track=st.selectbox("Track", list(TRACKS.keys()), key="calc_track")
    st.dataframe(pd.DataFrame({"Indicator":TRACKS[calc_track]["indicators"],"Status":"Requires reported values and source verification"}), width="stretch", hide_index=True)

else:
    st.markdown('<div class="trace-eyebrow">Transparent methods · no fabricated precision</div>', unsafe_allow_html=True)
    st.title("Method & safeguards")
    st.markdown("""
### Eight-stage research workflow
1. **Planner** turns the research question into track-specific subquestions.
2. **Researcher** searches public web results with bounded requests.
3. **Extractor** retrieves bounded HTML/PDF text, page/paragraph locations, dates and heuristic period candidates; optional model number/date extraction must exactly match a source quote.
4. **Verifier** validates quotation substrings and checks retrieval status/source candidates. Human review is still required to confirm that a source actually supports a claim or number.
5. **Triangulator** removes duplicate URLs/content fingerprints and flags detectable period differences. Different domains are not assumed independent.
6. **Analyst** optionally drafts a synthesis from supplied excerpts. Quote-checked number candidates can be manually confirmed and compared only when units and periods match; unsupported indicators stay unavailable.
7. **Skeptic** searches risk, adverse, and alternative-explanation terms.
8. **Reporter** assembles a cautious, exportable report with a falsification condition.

### Source and uncertainty rules
- Search snippets are discovery context, never proof.
- `page_fetched` means content was retrieved, not that a claim was verified.
- Publication date and reporting period are distinct. HTML metadata publication dates and heuristic period candidates are surfaced with provenance; verify both in the source.
- Model-drafted claims are kept only with exact quote matches in at least two domains; domain diversity is not proof of independence. Every draft remains review-required.
- Search failure and empty evidence remain visible; they are not interpreted as positive evidence.
- Company/sector track mappings are editable in `signaltrace/universe.py` and should be reviewed.
- No trading recommendation, target price, or market-outperformance prediction is produced.

### Reproducibility
Each report exports its request, timestamps, planned questions, queries, source URLs, retrieval status, extracted text, calculations, workflow trace, and limitations as JSON. The search provider and page fetcher are modular in `signaltrace/sources.py`.
""")
