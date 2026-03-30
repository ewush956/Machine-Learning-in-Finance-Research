# llm_panel.py

import math
import pandas as pd
import numpy as np
from shiny import ui, render, reactive

from context_builder import build_stock_context

# Constants -------------------------------------------------------------------

# How many API calls one user can make in a single browser session.
# A "session" in Shiny means from the moment the app loads in their browser
# until they close or refresh it. After this limit the input disables.
# 20 is generous for personal use — tighten it if usage grows.
MAX_CALLS_PER_SESSION = 20

# The Anthropic model to use for responses.
LLM_MODEL = "claude-sonnet-4-6"

# Maximum tokens Claude is allowed to generate per response.
# 1024 tokens is roughly 700-800 words which should be enough for 
# a thorough explanation without letting responses become essays.
MAX_TOKENS = 1024

# The system prompt is sent with every API call as a standing instruction
# to Claude. It defines Claude's role, tone, and constraints for this app.
# It is NOT part of the conversation history the user sees.
#
# Key design decisions here:
SYSTEM_PROMPT = """\
You are an educational finance assistant embedded in a stock analysis dashboard.
Your job is to help people with zero finance knowledge understand what the data means.

You will always receive a STOCK CONTEXT block with real computed metrics for the
stock currently on screen. Always refer to those specific numbers in your responses.
Never speak in generalities when actual data is available.

Guidelines:
- Use plain English. Avoid jargon. If you must use a term like "volatility" or
  "Sharpe ratio", explain it in the same sentence in everyday language.
- Be encouraging and patient. The user is learning, not trading professionally.
- Auto-summaries: 3 to 5 sentences. Follow-up answers: up to 8 sentences.
- When a number suggests risk, be honest but not alarming.
- Never give specific buy or sell advice. You explain what data means, not what to do.
"""

def _compute_metrics(
    df: pd.DataFrame,
    ticker: str,
    company_name: str,
    start_date: str,
    end_date: str,
) -> dict:
    """
    Computes all stock metrics needed by build_stock_context() from a raw
    yfinance history DataFrame.

    Returns a dictionary whose keys match exactly the parameter names of
    build_stock_context(). This means you can call:
        build_stock_context(**_compute_metrics(...))
    and it will work without any manual keyword mapping.

    Parameters
    ----------
    df : pd.DataFrame
        Raw yfinance history DataFrame. Must have a "Close" column and a
        DatetimeIndex. This is exactly what history_df() returns in server.py.

    ticker : str
        Stock symbol, e.g. "NVDA". Passed through to the output dict unchanged.

    company_name : str
        Full company name from ticker_info(). Passed through unchanged.

    start_date : str
        "YYYY-MM-DD" string for the period start. Passed through unchanged.

    end_date : str
        "YYYY-MM-DD" string for the period end. Passed through unchanged.

    Returns
    -------
    dict
        All keys needed by build_stock_context(). If df is empty or invalid,
        returns safe fallback values (zeros and NaN for Sharpe) so the rest
        of the app never crashes on missing data.
    """

    # The fallback dict is returned immediately if the data isn't usable.
    # Every numeric field defaults to 0.0 except Sharpe, which defaults to
    # float("nan") because 0.0 is a valid Sharpe ratio but NaN means
    # "could not be computed".
    fallback = dict(
        ticker=ticker,
        company_name=company_name,
        start_date=start_date,
        end_date=end_date,
        period_return_pct=0.0,
        ann_vol_pct=0.0,
        sharpe_ratio=float("nan"),
        avg_daily_move_pct=0.0,
        best_day_pct=0.0,
        worst_day_pct=0.0,
        trading_days=0,
    )

    if df is None or df.empty or "Close" not in df.columns:
        return fallback

    close = df["Close"].dropna()

    # Need at least 2 data points to compute any meaningful return or change.
    if len(close) < 2:
        return fallback

    # pct_change() computes day-over-day % change as a decimal.
    # e.g. price goes 100 → 102, pct_change = 0.02 (meaning +2%)
    # dropna() removes the first row which is always NaN
    # (there's no "previous day" for the first data point)
    daily_returns = close.pct_change().dropna()

    # Total return from first to last close, as a percentage.
    # e.g. 100 → 142.3 gives (142.3/100 - 1) * 100 = +42.3
    period_return_pct = float((close.iloc[-1] / close.iloc[0] - 1) * 100)

    # Annualized volatility: how much the stock typically swings per year.
    # .std() gives the standard deviation of daily returns (in decimal form).
    # Multiplying by sqrt(252) scales it from a daily figure to a yearly one.
    # Multiplying by 100 converts decimal to percentage.
    # 252 is the approximate number of trading days in a calendar year.
    ann_vol_pct = float(daily_returns.std() * math.sqrt(252) * 100)

    # Average daily move: the mean of all daily % changes over the period.
    # Slightly positive even in flat markets due to how compounding works.
    avg_daily_move_pct = float(daily_returns.mean() * 100)

    # Best and worst single trading days in the period.
    # .max() and .min() find the largest and smallest values in the series.
    # Multiplying by 100 converts decimal to percentage.
    best_day_pct = float(daily_returns.max() * 100)
    worst_day_pct = float(daily_returns.min() * 100)

    # Trading days = number of rows with valid Close prices.
    # This is NOT the same as calendar days — markets are closed on
    # weekends and holidays, so a full year is ~252 days, not 365.
    trading_days = len(close)

    # ── Sharpe Ratio ──────────────────────────────────────────────────────────
    # The Sharpe ratio measures return relative to risk.
    # Formula: sqrt(252) * mean(excess_returns) / std(excess_returns)
    #
    # "Excess return" means return above the risk-free rate — roughly the
    # return you'd get from a government savings account risk-free.
    # We use 2% annual (0.02) as a conventional baseline.
    #
    # Converting annual 2% to a daily rate:
    # (1 + 0.02)^(1/252) - 1 ≈ 0.0000789 per day
    # This is more mathematically correct than just dividing 0.02/252.
    rf_daily = (1.0 + 0.02) ** (1.0 / 252.0) - 1.0
    excess_returns = daily_returns - rf_daily

    std_excess = float(excess_returns.std())

    # Guard against division by zero (happens if all returns are identical,
    # e.g. a stock that didn't move at all in the period).
    if std_excess > 0 and math.isfinite(std_excess):
        sharpe_ratio = float(math.sqrt(252) * excess_returns.mean() / std_excess)
    else:
        sharpe_ratio = float("nan")

    return dict(
        ticker=ticker,
        company_name=company_name,
        start_date=start_date,
        end_date=end_date,
        period_return_pct=period_return_pct,
        ann_vol_pct=ann_vol_pct,
        sharpe_ratio=sharpe_ratio,
        avg_daily_move_pct=avg_daily_move_pct,
        best_day_pct=best_day_pct,
        worst_day_pct=worst_day_pct,
        trading_days=trading_days,
    )