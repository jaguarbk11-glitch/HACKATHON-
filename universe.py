from __future__ import annotations

TRACKS = {
    "Track A — Banking and NBFCs": {
        "signals": ["loan and deposit growth", "asset quality and NPA", "credit costs and provisioning", "capital adequacy", "net interest margin", "liquidity and funding"],
        "indicators": ["Loan growth vs deposit growth", "Gross/net NPA trend", "Credit cost and provisions", "Capital adequacy ratio", "Net interest margin", "Liquidity / funding profile"],
    },
    "Track B — Energy, Power and Renewables": {
        "signals": ["capacity additions and utilization", "power demand and generation", "fuel costs and input prices", "receivables and working capital", "project delays and capital expenditure", "policy and commodity exposure"],
        "indicators": ["Capacity and utilization", "Demand / generation", "Fuel and input costs", "Receivables and working capital", "Capex and project schedule", "Policy / commodity exposure"],
    },
    "Track C — Consumer, FMCG and Retail": {
        "signals": ["revenue and volume growth", "pricing and demand", "receivables and inventory", "distribution and channel shifts", "quick commerce", "competitor and industry comparison"],
        "indicators": ["Revenue vs disclosed volume growth", "Pricing and demand commentary", "Receivables / inventory vs revenue", "Distribution and channel shifts", "Quick-commerce updates", "Peer comparison"],
    },
    "Track D — Pharma and Healthcare": {
        "signals": ["product and segment revenue growth", "regulatory approvals and observations", "patent expiries and product concentration", "research and development expenditure", "manufacturing and compliance risks", "competitor and industry developments"],
        "indicators": ["Product / segment revenue", "Regulatory approvals and observations", "Patent / concentration exposure", "R&D expenditure", "Manufacturing and compliance", "Peer developments"],
    },
}

# Editable starter universe; validate current constituents/sectors before relying on it.
# A company appears under one research track based on a practical primary-sector mapping.
NIFTY50 = [
    {"company":"Adani Enterprises","ticker":"ADANIENT","exchange":"NSE","sector":"Diversified","track":None},
    {"company":"Adani Ports and Special Economic Zone","ticker":"ADANIPORTS","exchange":"NSE","sector":"Ports","track":None},
    {"company":"Apollo Hospitals Enterprise","ticker":"APOLLOHOSP","exchange":"NSE","sector":"Healthcare","track":"Track D — Pharma and Healthcare"},
    {"company":"Asian Paints","ticker":"ASIANPAINT","exchange":"NSE","sector":"Consumer","track":"Track C — Consumer, FMCG and Retail"},
    {"company":"Axis Bank","ticker":"AXISBANK","exchange":"NSE","sector":"Banking","track":"Track A — Banking and NBFCs"},
    {"company":"Bajaj Auto","ticker":"BAJAJ-AUTO","exchange":"NSE","sector":"Automobiles","track":None},
    {"company":"Bajaj Finance","ticker":"BAJFINANCE","exchange":"NSE","sector":"NBFC","track":"Track A — Banking and NBFCs"},
    {"company":"Bajaj Finserv","ticker":"BAJAJFINSV","exchange":"NSE","sector":"Financial services","track":"Track A — Banking and NBFCs"},
    {"company":"Bharat Electronics","ticker":"BEL","exchange":"NSE","sector":"Defence","track":None},
    {"company":"Bharti Airtel","ticker":"BHARTIARTL","exchange":"NSE","sector":"Telecom","track":None},
    {"company":"Cipla","ticker":"CIPLA","exchange":"NSE","sector":"Pharma","track":"Track D — Pharma and Healthcare"},
    {"company":"Coal India","ticker":"COALINDIA","exchange":"NSE","sector":"Energy","track":"Track B — Energy, Power and Renewables"},
    {"company":"Dr. Reddy's Laboratories","ticker":"DRREDDY","exchange":"NSE","sector":"Pharma","track":"Track D — Pharma and Healthcare"},
    {"company":"Eternal","ticker":"ETERNAL","exchange":"NSE","sector":"Consumer and technology","track":"Track C — Consumer, FMCG and Retail"},
    {"company":"Eicher Motors","ticker":"EICHERMOT","exchange":"NSE","sector":"Automobiles","track":None},
    {"company":"Grasim Industries","ticker":"GRASIM","exchange":"NSE","sector":"Materials","track":None},
    {"company":"HCL Technologies","ticker":"HCLTECH","exchange":"NSE","sector":"IT","track":None},
    {"company":"HDFC Bank","ticker":"HDFCBANK","exchange":"NSE","sector":"Banking","track":"Track A — Banking and NBFCs"},
    {"company":"HDFC Life Insurance","ticker":"HDFCLIFE","exchange":"NSE","sector":"Insurance","track":"Track A — Banking and NBFCs"},
    {"company":"Hero MotoCorp","ticker":"HEROMOTOCO","exchange":"NSE","sector":"Automobiles","track":None},
    {"company":"Hindalco Industries","ticker":"HINDALCO","exchange":"NSE","sector":"Metals","track":None},
    {"company":"Hindustan Unilever","ticker":"HINDUNILVR","exchange":"NSE","sector":"FMCG","track":"Track C — Consumer, FMCG and Retail"},
    {"company":"ICICI Bank","ticker":"ICICIBANK","exchange":"NSE","sector":"Banking","track":"Track A — Banking and NBFCs"},
    {"company":"IndusInd Bank","ticker":"INDUSINDBK","exchange":"NSE","sector":"Banking","track":"Track A — Banking and NBFCs"},
    {"company":"Infosys","ticker":"INFY","exchange":"NSE","sector":"IT","track":None},
    {"company":"ITC","ticker":"ITC","exchange":"NSE","sector":"Consumer","track":"Track C — Consumer, FMCG and Retail"},
    {"company":"JSW Steel","ticker":"JSWSTEEL","exchange":"NSE","sector":"Steel","track":None},
    {"company":"Jio Financial Services","ticker":"JIOFIN","exchange":"NSE","sector":"Financial services","track":"Track A — Banking and NBFCs"},
    {"company":"Kotak Mahindra Bank","ticker":"KOTAKBANK","exchange":"NSE","sector":"Banking","track":"Track A — Banking and NBFCs"},
    {"company":"Larsen & Toubro","ticker":"LT","exchange":"NSE","sector":"Industrials","track":None},
    {"company":"Mahindra & Mahindra","ticker":"M&M","exchange":"NSE","sector":"Automobiles","track":None},
    {"company":"Maruti Suzuki India","ticker":"MARUTI","exchange":"NSE","sector":"Automobiles","track":None},
    {"company":"Nestle India","ticker":"NESTLEIND","exchange":"NSE","sector":"FMCG","track":"Track C — Consumer, FMCG and Retail"},
    {"company":"NTPC","ticker":"NTPC","exchange":"NSE","sector":"Power","track":"Track B — Energy, Power and Renewables"},
    {"company":"Oil and Natural Gas Corporation","ticker":"ONGC","exchange":"NSE","sector":"Energy","track":"Track B — Energy, Power and Renewables"},
    {"company":"Power Grid Corporation of India","ticker":"POWERGRID","exchange":"NSE","sector":"Power","track":"Track B — Energy, Power and Renewables"},
    {"company":"Reliance Industries","ticker":"RELIANCE","exchange":"NSE","sector":"Energy and retail","track":"Track B — Energy, Power and Renewables"},
    {"company":"SBI Life Insurance","ticker":"SBILIFE","exchange":"NSE","sector":"Insurance","track":"Track A — Banking and NBFCs"},
    {"company":"Shriram Finance","ticker":"SHRIRAMFIN","exchange":"NSE","sector":"NBFC","track":"Track A — Banking and NBFCs"},
    {"company":"State Bank of India","ticker":"SBIN","exchange":"NSE","sector":"Banking","track":"Track A — Banking and NBFCs"},
    {"company":"Sun Pharmaceutical Industries","ticker":"SUNPHARMA","exchange":"NSE","sector":"Pharma","track":"Track D — Pharma and Healthcare"},
    {"company":"Tata Consumer Products","ticker":"TATACONSUM","exchange":"NSE","sector":"FMCG","track":"Track C — Consumer, FMCG and Retail"},
    {"company":"Tata Motors","ticker":"TATAMOTORS","exchange":"NSE","sector":"Automobiles","track":None},
    {"company":"Tata Steel","ticker":"TATASTEEL","exchange":"NSE","sector":"Steel","track":None},
    {"company":"TCS","ticker":"TCS","exchange":"NSE","sector":"IT","track":None},
    {"company":"Tech Mahindra","ticker":"TECHM","exchange":"NSE","sector":"IT","track":None},
    {"company":"Titan Company","ticker":"TITAN","exchange":"NSE","sector":"Consumer","track":"Track C — Consumer, FMCG and Retail"},
    {"company":"Trent","ticker":"TRENT","exchange":"NSE","sector":"Retail","track":"Track C — Consumer, FMCG and Retail"},
    {"company":"UltraTech Cement","ticker":"ULTRACEMCO","exchange":"NSE","sector":"Cement","track":None},
    {"company":"Wipro","ticker":"WIPRO","exchange":"NSE","sector":"IT","track":None},
]


def companies_for_track(track: str) -> list[dict[str, str | None]]:
    return [item for item in NIFTY50 if item["track"] == track]
