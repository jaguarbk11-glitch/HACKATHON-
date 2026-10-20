from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import socket
import time
from io import BytesIO
from datetime import datetime, timezone
from typing import Callable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .models import Evidence, ResearchRequest

USER_AGENT = "SignalTraceAI/0.1 (public research; respectful low-volume access)"


def domain_for(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except ValueError:
        return "unknown"


def classify_source(url: str) -> str:
    domain = domain_for(url)
    if any(domain == root or domain.endswith("." + root) for root in (
        "nseindia.com", "bseindia.com", "sebi.gov.in", "rbi.org.in", "mca.gov.in", "mospi.gov.in", "cea.nic.in", "mnre.gov.in", "pharma-dept.gov.in"
    )):
        return "primary_regulatory_or_exchange"
    if domain.endswith(".gov.in") or domain.endswith(".nic.in"):
        return "public_sector_or_regulatory"
    return "secondary_or_unclassified"


def _publication_date(soup) -> tuple[str | None, str]:
    for selector, attribute in (("meta[property='article:published_time']", "content"),
                                ("meta[name='datePublished']", "content"),
                                ("meta[name='pubdate']", "content"),
                                ("meta[name='publish-date']", "content"),
                                ("time[datetime]", "datetime")):
        node = soup.select_one(selector)
        raw = node.get(attribute) if node else None
        if raw:
            try:
                parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
                return parsed.date().isoformat(), f"html:{selector}"
            except ValueError:
                match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", str(raw))
                if match:
                    return match.group(1), f"html:{selector}:date_only"
    for node in soup.find_all("script", attrs={"type": "application/ld+json"}, limit=4):
        try:
            payload = json.loads(node.string or node.get_text())
        except (json.JSONDecodeError, TypeError):
            continue
        objects = payload if isinstance(payload, list) else [payload]
        for obj in objects:
            if isinstance(obj, dict) and obj.get("datePublished"):
                raw = str(obj["datePublished"])
                try:
                    return datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat(), "json-ld:datePublished"
                except ValueError:
                    continue
    return None, "unavailable"


def _period_candidate(text: str) -> str | None:
    patterns = (
        r"\bQ[1-4]\s*FY\s*20\d{2}\b", r"\bQ[1-4]\s*20\d{2}\b",
        r"\bFY\s*20\d{2}\b", r"\bfinancial year\s+20\d{2}(?:\s*[-–/]\s*\d{2,4})?\b",
        r"\b(?:year|quarter|half year) ended\s+(?:on\s+)?[A-Z][a-z]+\s+\d{1,2},?\s+20\d{2}\b",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(0)
    return None


def is_public_http_url(url: str) -> bool:
    """Reject local/private destinations and unusual ports before making requests."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
            return False
        if parsed.port and parsed.port not in (80, 443):
            return False
        host = parsed.hostname.rstrip(".").lower()
        if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
            return False
        try:
            addresses = [ipaddress.ip_address(host)]
        except ValueError:
            addresses = [ipaddress.ip_address(item[4][0]) for item in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)]
        return bool(addresses) and all(address.is_global for address in addresses)
    except (ValueError, OSError):
        return False


class SearchProvider:
    """Search adapter. DDGS is optional at import time and network calls are bounded."""

    def search(self, query: str, limit: int = 5) -> list[dict[str, str]]:
        try:
            from ddgs import DDGS
        except ImportError as exc:
            raise RuntimeError("Search dependency ddgs is not installed. Install requirements.txt first.") from exc
        try:
            with DDGS(timeout=8) as client:
                results = client.text(query, max_results=limit)
                return [
                    {"title": str(row.get("title") or "Untitled result"),
                     "url": str(row.get("href") or row.get("url") or ""),
                     "snippet": str(row.get("body") or "")}
                    for row in results if row.get("href") or row.get("url")
                ]
        except Exception as exc:
            raise RuntimeError(f"Search request failed: {type(exc).__name__}: {exc}") from exc


class PageFetcher:
    def __init__(self, timeout: float = 8.0, max_chars: int = 12000):
        self.timeout = timeout
        self.max_chars = max_chars
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept": "text/html,application/pdf;q=0.9,*/*;q=0.8"})

    def fetch(self, url: str) -> dict[str, str | None]:
        current_url = url
        try:
            response = None
            for _ in range(4):
                if not is_public_http_url(current_url):
                    return {"text": "", "status": "blocked_non_public_or_invalid_url", "publication_date": None, "date_basis": "unavailable", "period_candidate": None, "title": None, "paragraphs": [], "url": current_url}
                response = self.session.get(current_url, timeout=self.timeout, allow_redirects=False, stream=True)
                if response.is_redirect or response.is_permanent_redirect:
                    location = response.headers.get("location")
                    response.close()
                    if not location:
                        return {"text": "", "status": "redirect_without_location", "publication_date": None, "date_basis": "unavailable", "period_candidate": None, "title": None, "paragraphs": [], "url": current_url}
                    current_url = urljoin(current_url, location)
                    continue
                break
            else:
                return {"text": "", "status": "redirect_limit_exceeded", "publication_date": None, "date_basis": "unavailable", "period_candidate": None, "title": None, "paragraphs": [], "url": current_url}
            if response is None:
                return {"text": "", "status": "fetch_failed:empty_response", "publication_date": None, "date_basis": "unavailable", "period_candidate": None, "title": None, "paragraphs": [], "url": current_url}
            content_type = response.headers.get("content-type", "").lower()
            if response.status_code >= 400:
                response.close()
                return {"text": "", "status": f"http_{response.status_code}", "publication_date": None, "date_basis": "unavailable", "period_candidate": None, "title": None, "paragraphs": [], "url": current_url}
            chunks = []
            total = 0
            for chunk in response.iter_content(chunk_size=64_000):
                if not chunk:
                    continue
                remaining = 2_000_000 - total
                chunks.append(chunk[:remaining])
                total += min(len(chunk), remaining)
                if total >= 2_000_000:
                    break
            response.close()
            raw = b"".join(chunks)
            if "pdf" in content_type or raw.startswith(b"%PDF"):
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(BytesIO(raw), strict=False)
                    paragraphs = []
                    page_texts = []
                    for index, page in enumerate(reader.pages[:35]):
                        page_text = page.extract_text() or ""
                        page_texts.append(page_text)
                        paragraphs.extend(f"[PDF page {index + 1}] {part.strip()}" for part in re.split(r"\n\s*\n", page_text) if len(part.strip()) > 45)
                    text = re.sub(r"\s+", " ", " ".join(page_texts))[: self.max_chars]
                    metadata_title = str(reader.metadata.title).strip() if reader.metadata and reader.metadata.title else None
                    return {"text": text, "status": "page_fetched" if text else "pdf_text_unavailable", "publication_date": None,
                            "date_basis": "unavailable_pdf_metadata_requires_review", "period_candidate": _period_candidate(text[:7000]),
                            "title": metadata_title, "paragraphs": paragraphs[:300], "url": current_url}
                except Exception as exc:
                    return {"text": "", "status": f"pdf_extraction_failed:{type(exc).__name__}", "publication_date": None,
                            "date_basis": "unavailable", "period_candidate": None, "title": None, "paragraphs": [], "url": current_url}
            soup = BeautifulSoup(raw, "html.parser")
            date_value, date_basis = _publication_date(soup)
            title = soup.title.get_text(" ", strip=True) if soup.title else None
            for element in soup(["script", "style", "noscript", "svg", "nav", "footer"]):
                element.decompose()
            paragraphs = [re.sub(r"\s+", " ", node.get_text(" ", strip=True)) for node in soup.find_all(["p", "li"]) if len(node.get_text(strip=True)) > 35]
            text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))[: self.max_chars]
            return {"text": text, "status": "page_fetched" if text else "empty_page", "publication_date": date_value,
                    "date_basis": date_basis, "period_candidate": _period_candidate((title or "") + " " + text[:5000]),
                    "title": title, "paragraphs": paragraphs[:300], "url": current_url}
        except requests.RequestException as exc:
            return {"text": "", "status": f"fetch_failed:{type(exc).__name__}", "publication_date": None, "date_basis": "unavailable", "period_candidate": None, "title": None, "paragraphs": [], "url": url}


class EvidenceCollector:
    def __init__(self, search: SearchProvider | None = None, fetcher: PageFetcher | None = None,
                 delay: float = 0.12, max_sources: int = 20):
        self.search_provider = search or SearchProvider()
        self.fetcher = fetcher or PageFetcher()
        self.delay = delay
        self.max_sources = max_sources

    def collect(self, request: ResearchRequest, queries: list[tuple[str, str]], per_query: int = 4,
                progress: Callable[[str, str], None] | None = None) -> tuple[list[Evidence], list[str]]:
        evidence: list[Evidence] = []
        errors: list[str] = []
        seen_urls: set[str] = set()
        seen_content: set[str] = set()
        total_queries = len(queries)
        for query_index, (category, query) in enumerate(queries, start=1):
            source_group = category.split(" · ", maxsplit=1)[0]
            signal_category = category.split(" · ", maxsplit=1)[1] if " · " in category else category
            if len(evidence) >= self.max_sources:
                errors.append(f"Source cap reached ({self.max_sources}); remaining search angles were not attempted.")
                break
            if progress:
                progress("Researcher", f"Searching query {query_index}/{total_queries} · {source_group}")
            try:
                results = self.search_provider.search(query, per_query)
            except Exception as exc:
                errors.append(f"{query}: {exc}")
                continue
            for result in results:
                if len(evidence) >= self.max_sources:
                    break
                url = result.get("url", "").strip()
                if not url.startswith(("https://", "http://")) or url in seen_urls:
                    continue
                seen_urls.add(url)
                if progress:
                    progress("Researcher", f"Fetching source for query {query_index}/{total_queries} · {domain_for(url)}")
                page = self.fetcher.fetch(url)
                text = str(page["text"] or "")
                fingerprint = hashlib.sha256(text[:5000].lower().encode("utf-8")).hexdigest() if text else ""
                if fingerprint and fingerprint in seen_content:
                    continue
                if fingerprint:
                    seen_content.add(fingerprint)
                title = result.get("title", "Untitled result")
                snippet = result.get("snippet", "")
                status = str(page["status"])
                limitations = []
                if not text:
                    limitations.append("No page text was extracted; search snippet is discovery context only, not verified evidence.")
                else:
                    limitations.append("Page retrieval does not by itself verify that the source supports a financial claim.")
                evidence.append(Evidence(
                    company=request.company, track=request.track, signal_category=signal_category,
                    source_title=str(page.get("title") or title), publisher=domain_for(str(page.get("url") or url)), original_url=str(page.get("url") or url),
                    snippet=snippet, search_query=query, source_type=classify_source(str(page.get("url") or url)),
                    publication_date=page.get("publication_date"), extracted_text=text,
                    verification_status=status, limitations=limitations, content_fingerprint=fingerprint,
                    source_group=source_group, date_basis=str(page.get("date_basis") or "unavailable"),
                    reporting_period_candidate=page.get("period_candidate"),
                    relevant_passages=[str(part) for part in (page.get("paragraphs") or [])[:300]],
                    passage_locator="HTML paragraph order; original page layout may differ",
                ))
                if self.delay:
                    time.sleep(self.delay)
        return evidence, errors
