# SignalTrace AI

SignalTrace is an evidence-first Streamlit research workbench for the BITS Pilani Hyderabad Campus ATMOS 2026 “Finding the Next Signal” challenge. It turns a company question into track-specific public-web searches, preserves source URLs and retrieval metadata, highlights uncertainty, and exports a reproducible evidence bundle.

> Research software for educational use only. It is not investment advice. Search results are not verified claims, and this application does not recommend buying or selling securities.

## Windows setup (beginner friendly)

1. Open this folder in VS Code.
2. Open **Terminal → New Terminal**.
3. Create and activate a virtual environment (use `python` or `py`, depending on which Python launcher is installed):
   - PowerShell: `python -m venv .venv`
   - PowerShell: `.\.venv\Scripts\Activate.ps1`
   - If script execution is blocked, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, then activate again.
4. Install dependencies: `python -m pip install -r requirements.txt`
5. (Optional) Copy `.env.example` to `.env` and fill in your OpenAI-compatible provider settings locally. Set `SIGNALTRACE_ENABLE_LLM=true` and `SIGNALTRACE_LLM_API_KEY` to enable model-generated research drafts. Do not share or commit `.env`.
6. Start the dashboard: `python -m streamlit run app.py`
7. Open the local address printed in the terminal (typically `http://localhost:8501`).

If neither launcher works, install Python 3.11+ from python.org and enable “Add Python to PATH” during setup. In VS Code, select the Python interpreter from `.venv`. The app requires internet access for search and page retrieval. Search providers may throttle, block, or change their interfaces; failures are reported in the run.

## What works

- Four research tracks with sector-specific query signals and indicator checklists.
- Company, ticker, exchange, sector, reporting period, and question inputs.
- An editable 50-company starter universe, track mappings, and explicitly limited multi-company research batches (max 10 runs per batch).
- Eight auditable stages: Planner, Researcher, Extractor, Verifier, Triangulator, Analyst, Skeptic, Reporter.
- Search adapter using `ddgs`; bounded HTTP page retrieval using `requests` and BeautifulSoup.
- Text extraction from accessible HTML and text-based PDFs (bounded to 2 MB and 35 pages); image-only/scanned PDFs need OCR and remain unavailable.
- URL and exact extracted-content deduplication, source-domain/type grouping, retrieval-status labels, publication-date metadata, and explicit limitations. The fetcher rejects private/local destinations and validates redirects.
- Optional OpenAI-compatible grounded analyst draft with exact-substring citation checks, multi-domain quote candidates, quote-linked number candidates, source-quoted timeline events, counterevidence, alternatives, and falsification proposals. All model outputs remain drafts; the dashboard can raise evidence strength only after per-citation review and a user attestation about source independence.
- Track-oriented evidence visualization, evidence table, extracted text inspection, JSON report export, and CSV evidence export.
- Cited revenue, receivables, and inventory growth calculator with period-frequency, missing/negative/zero input, and citation checks.
- Unit tests for calculations, period/citation edge cases, and workflow behavior.

## Important limitations

- The default workflow runs without an LLM and does not need an API key. Optional LLM synthesis requires a user-configured API key/model. Provider costs, data handling, and service terms are the user's responsibility; retrieved excerpts are sent to the configured provider when enabled.
- A model draft is not a verified finding. Exact-substring checks reject quotations absent from supplied excerpts, but do not verify that a quote semantically supports an interpretation, that sources are independent, or that extracted values are correct.
- Strong/Moderate status is gated by human review checkboxes and the user's explicit independence attestation. This is an auditable user assertion, not an automatic independent audit.
- `page_fetched` means page text was retrieved, **not** that a source supports a claim. Search snippets are discovery leads only. Human review of source context is required.
- Number-like observations are quote-matched candidate extractions only. Financial calculations remain unavailable until values are independently checked and entered in **Calculator**. User-entered URLs and values are not independently verified by the calculator.
- The timeline combines publication-date metadata and, when model synthesis is enabled, exact-quote-matched event-date candidates. Publication date and reporting period are separate. Verify both in the source.
- Exact-content deduplication cannot catch every syndicated article. Different domains are not assumed independent. Tone is not treated as evidence of factual support.
- The NIFTY 50 list and classifications are a configurable starter snapshot, not a live index feed. Verify current constituents and company mappings before presenting coverage.
- Automated evidence strength remains **Weak** until human source review; the confidence label is not the probability that a hypothesis is true.

## Project layout

- `app.py` — Streamlit dashboard and exports.
- `signaltrace/models.py` — typed request, evidence, calculation, and report models.
- `signaltrace/universe.py` — track definitions and editable universe.
- `signaltrace/sources.py` — search and page-retrieval connectors.
- `signaltrace/pipeline.py` — staged workflow and cautious reporting.
- `signaltrace/calculations.py` — cited financial calculation helpers.
- `tests/` — automated tests.

## Run tests

With the virtual environment activated: `python -m pytest -q` (or `.\.venv\Scripts\python.exe -m pytest -q`).

## Extend safely

Implement a new provider behind the `SearchProvider.search()` interface in `signaltrace/sources.py`. Keep retrieved source text distinct from interpretations. For additional calculations, record formula, units, periods, inputs, and URLs, reject incomparable inputs, and add tests. For institutional use, add authenticated exchange/company document APIs, PDF extraction, robust source-identity checks, human claim verification, rate-limit/backoff controls, and live constituent validation before relying on reports.
