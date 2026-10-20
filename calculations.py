from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

from .models import Calculation


def _period_kind(label: str) -> str | None:
    normalized = label.strip().lower()
    if re.search(r"\bq[1-4]\b", normalized) or "quarter" in normalized:
        return "quarter"
    if re.search(r"\bh[12]\b", normalized) or "half-year" in normalized or "half year" in normalized:
        return "half-year"
    if re.search(r"\bfy\s*\d{2,4}\b", normalized) or re.search(r"\bfinancial year\b", normalized):
        return "year"
    if re.search(r"\b\d{4}\b", normalized):
        return "year"
    return None


def _period_slot(label: str) -> str | None:
    normalized = label.strip().lower()
    quarter = re.search(r"\b(q[1-4])\b", normalized)
    if quarter:
        return quarter.group(1)
    half = re.search(r"\b(h[12])\b", normalized)
    if half:
        return half.group(1)
    return "full-period" if _period_kind(label) == "year" else None


def _growth(name: str, current: float | None, previous: float | None, unit: str,
            current_period: str, previous_period: str, current_url: str, previous_url: str) -> Calculation:
    inputs: dict[str, Any] = {"current": current, "previous": previous}
    periods = {"current": current_period, "previous": previous_period}
    urls = [url for url in (current_url, previous_url) if url]
    if current is None or previous is None:
        return Calculation(name, "unavailable", "(current - previous) / previous * 100", None, "%", inputs, periods, urls, "Both values are required; the calculator does not verify them against cited pages.")
    if not current_url.startswith(("https://", "http://")) or not previous_url.startswith(("https://", "http://")):
        return Calculation(name, "unavailable", "(current - previous) / previous * 100", None, "%", inputs, periods, urls, "A source URL for each input is required; user-provided URLs are not independently verified by this calculator.")
    if previous == 0:
        return Calculation(name, "unavailable", "(current - previous) / previous * 100", None, "%", inputs, periods, urls, "Prior-period value is zero; growth is undefined.")
    if current < 0 or previous < 0:
        return Calculation(name, "unavailable", "(current - previous) / previous * 100", None, "%", inputs, periods, urls, "Negative inputs are not accepted for this growth calculation.")
    if not current_period or not previous_period:
        return Calculation(name, "unavailable", "(current - previous) / previous * 100", None, "%", inputs, periods, urls, "Reporting periods are required to judge comparability.")
    current_kind, previous_kind = _period_kind(current_period), _period_kind(previous_period)
    if current_kind is None or previous_kind is None or current_kind != previous_kind:
        return Calculation(name, "unavailable", "(current - previous) / previous * 100", None, "%", inputs, periods, urls, "Period labels do not establish matching reporting frequencies; use comparable periods.")
    if _period_slot(current_period) != _period_slot(previous_period):
        return Calculation(name, "unavailable", "(current - previous) / previous * 100", None, "%", inputs, periods, urls, "Period labels refer to different quarters/half-years; compare matching periods.")
    note = ""
    status = "calculated"
    if current_period == previous_period:
        status = "unavailable"
        note = "Current and prior period labels are identical; enter distinct comparable periods."
    value = ((current - previous) / previous) * 100 if status == "calculated" else None
    return Calculation(name, status, "(current - previous) / previous * 100", value, "%", inputs, periods, urls, note)


def revenue_growth(current: float | None, previous: float | None, current_period: str = "", previous_period: str = "", current_url: str = "", previous_url: str = "") -> Calculation:
    return _growth("Revenue growth", current, previous, "currency", current_period, previous_period, current_url, previous_url)


def receivables_growth(current: float | None, previous: float | None, current_period: str = "", previous_period: str = "", current_url: str = "", previous_url: str = "") -> Calculation:
    return _growth("Receivables growth", current, previous, "currency", current_period, previous_period, current_url, previous_url)


def inventory_growth(current: float | None, previous: float | None, current_period: str = "", previous_period: str = "", current_url: str = "", previous_url: str = "") -> Calculation:
    return _growth("Inventory growth", current, previous, "currency", current_period, previous_period, current_url, previous_url)


def reviewed_observation_growth(current: dict[str, Any], previous: dict[str, Any], reviewed_ids: set[str]) -> Calculation:
    """Calculate growth only after the user confirms both quote-linked observations."""
    name = f"{current.get('metric') or 'Metric'} growth"
    current_id, previous_id = str(current.get("evidence_id", "")), str(previous.get("evidence_id", ""))
    current_unit = str(current.get("unit_as_reported", "")).strip()
    previous_unit = str(previous.get("unit_as_reported", "")).strip()
    urls = [str(current.get("url", "")), str(previous.get("url", ""))]
    if not current_id or not previous_id or not {current_id, previous_id}.issubset(reviewed_ids):
        return Calculation(name, "unavailable", "(current - previous) / previous * 100", None, "%", {}, {}, urls,
                           "Open both cited sources and mark both observations reviewed before calculating.")
    if str(current.get("metric", "")).strip().lower() != str(previous.get("metric", "")).strip().lower():
        return Calculation(name, "unavailable", "(current - previous) / previous * 100", None, "%", {}, {}, urls,
                           "Metric labels do not match; do not compare different financial measures.")
    if not current_unit or current_unit.casefold() != previous_unit.casefold():
        return Calculation(name, "unavailable", "(current - previous) / previous * 100", None, "%", {}, {}, urls,
                           "Units must match and be explicitly present in both observations.")

    def parse_number(raw: Any) -> float | None:
        text = str(raw or "").strip().replace(",", "")
        if not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", text):
            return None
        try:
            number = Decimal(text)
            return float(number) if number.is_finite() else None
        except InvalidOperation:
            return None

    current_value = parse_number(current.get("value_as_reported"))
    previous_value = parse_number(previous.get("value_as_reported"))
    current_period = str(current.get("period_as_reported", ""))
    previous_period = str(previous.get("period_as_reported", ""))
    result = _growth(name, current_value, previous_value, current_unit, current_period, previous_period, urls[0], urls[1])
    result.inputs["unit"] = current_unit
    result.inputs["current_source_quote"] = current.get("quote", "")
    result.inputs["previous_source_quote"] = previous.get("quote", "")
    if current_value is None or previous_value is None:
        result.status = "unavailable"
        result.value = None
        result.note = "Values are not simple, unambiguous numbers; normalize manually without changing source units."
    result.note = (result.note + " Calculated from model-extracted, quote-matched candidates after user review; source interpretation remains the user's responsibility.").strip()
    return result


def growth_comparison(company_growth: float | None, peer_growth: float | None, company_period: str, peer_period: str,
                      company_url: str = "", peer_url: str = "") -> Calculation:
    inputs = {"company_growth_pct": company_growth, "peer_growth_pct": peer_growth}
    urls = [url for url in (company_url, peer_url) if url]
    if company_growth is None or peer_growth is None:
        status, value, note = "unavailable", None, "Both comparable, source-backed growth values are required."
    elif not company_url.startswith(("https://", "http://")) or not peer_url.startswith(("https://", "http://")):
        status, value, note = "unavailable", None, "A source URL for each input is required; URLs are not independently verified."
    elif not company_period or company_period != peer_period:
        status, value, note = "unavailable", None, "Company and peer reporting periods must match exactly."
    else:
        status, value, note = "calculated", company_growth - peer_growth, "Difference in percentage points."
    return Calculation("Company vs peer growth", status, "company growth (%) - peer growth (%)", value, "percentage points", inputs,
                       {"company": company_period, "peer": peer_period}, urls, note)


def unavailable_track_indicators(track: str, indicators: list[str]) -> list[Calculation]:
    return [Calculation(name, "unavailable", "Not calculated: no structured, source-verified inputs supplied.", None, "", {}, {}, [],
                        f"{track}: enter comparable data with a source URL; this research run does not infer numeric inputs from search snippets.")
            for name in indicators]
