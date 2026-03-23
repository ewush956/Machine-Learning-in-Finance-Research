import re

fuggin_stonks = {
    # Technology
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "NVIDIA": "NVDA",
    "Alphabet": "GOOGL",
    "Meta Platforms": "META",
    "Amazon": "AMZN",
    "Tesla": "TSLA",
    "Broadcom": "AVGO",
    "Taiwan Semiconductor": "TSM",
    "Samsung Electronics": "005930.KS",
    "ASML Holding": "ASML",
    "Intel": "INTC",
    "Advanced Micro Devices": "AMD",
    "Qualcomm": "QCOM",
    "Applied Materials": "AMAT",
    "Micron Technology": "MU",
    "Texas Instruments": "TXN",
    "Salesforce": "CRM",
    "Oracle": "ORCL",
    "SAP": "SAP",
    "Adobe": "ADBE",
    "Palantir Technologies": "PLTR",
    "Snowflake": "SNOW",
    "CrowdStrike": "CRWD",
    "ServiceNow": "NOW",
    "Shopify": "SHOP",
    "Cloudflare": "NET",
    "Datadog": "DDOG",
    "Palo Alto Networks": "PANW",
    "Workday": "WDAY",
    "Fortinet": "FTNT",
    "Intuit": "INTU",
    "Autodesk": "ADSK",
    "Zoom Video": "ZM",

    # Finance
    "JPMorgan Chase": "JPM",
    "Berkshire Hathaway": "BRK-B",
    "Visa": "V",
    "Mastercard": "MA",
    "Bank of America": "BAC",
    "Wells Fargo": "WFC",
    "Goldman Sachs": "GS",
    "Morgan Stanley": "MS",
    "BlackRock": "BLK",
    "American Express": "AXP",
    "Citigroup": "C",
    "Charles Schwab": "SCHW",
    "PayPal": "PYPL",
    "Coinbase": "COIN",

    # Healthcare & Pharma
    "UnitedHealth Group": "UNH",
    "Johnson & Johnson": "JNJ",
    "Eli Lilly": "LLY",
    "AbbVie": "ABBV",
    "Pfizer": "PFE",
    "Merck": "MRK",
    "Novo Nordisk": "NVO",
    "Abbott Laboratories": "ABT",
    "Thermo Fisher Scientific": "TMO",
    "Medtronic": "MDT",
    "CVS Health": "CVS",
    "Moderna": "MRNA",
    "Intuitive Surgical": "ISRG",
    "Boston Scientific": "BSX",

    # Consumer & Retail
    "Walmart": "WMT",
    "Costco": "COST",
    "Procter & Gamble": "PG",
    "Coca-Cola": "KO",
    "PepsiCo": "PEP",
    "McDonald's": "MCD",
    "Starbucks": "SBUX",
    "Nike": "NKE",
    "Home Depot": "HD",
    "Target": "TGT",
    "Lowe's": "LOW",
    "LVMH": "LVMUY",
    "Hermes International": "HESAY",
    "Ferrari": "RACE",

    # Energy
    "ExxonMobil": "XOM",
    "Chevron": "CVX",
    "Shell": "SHEL",
    "ConocoPhillips": "COP",
    "BP": "BP",
    "NextEra Energy": "NEE",
    "Enbridge": "ENB",
    "Canadian Natural Resources": "CNQ",

    # Industrials & Aerospace
    "Microsoft": "MSFT",
    "Caterpillar": "CAT",
    "Boeing": "BA",
    "Lockheed Martin": "LMT",
    "Raytheon Technologies": "RTX",
    "Honeywell": "HON",
    "Deere & Company": "DE",
    "General Electric": "GE",
    "3M": "MMM",
    "Union Pacific": "UNP",

    # Communications & Media
    "T-Mobile": "TMUS",
    "AT&T": "T",
    "Verizon": "VZ",
    "Walt Disney": "DIS",
    "Netflix": "NFLX",
    "Spotify": "SPOT",

    # Materials & Mining
    "BHP Group": "BHP",
    "Rio Tinto": "RIO",
    "Barrick Gold": "GOLD",
    "Freeport-McMoRan": "FCX",
    "Newmont": "NEM",

    # Real Estate
    "American Tower": "AMT",
    "Prologis": "PLD",
    "Simon Property Group": "SPG",

    # ETFs (Bonus)
    "S&P 500 ETF (SPY)": "SPY",
    "Nasdaq-100 ETF (QQQ)": "QQQ",
    "Total Market ETF (VTI)": "VTI",
}

def test_query(query : str):
    query = query.strip().lower()
    pattern = re.compile(f"^{re.escape(query)}", re.IGNORECASE)
    results = {
        name : ticker
        for name, ticker in fuggin_stonks.items()
        if pattern.search(name) or pattern.search(ticker)
    }
    if results:
        return results
    else:
        return f"No results found in query: '{query}'"

print(test_query("aap"))