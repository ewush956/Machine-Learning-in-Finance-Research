# context_builder.py
#
# Purpose:
#   Converts computed stock metrics into a plain-text context block
#   that gets injected into every Claude API call. This is how Claude
#   "knows" what stock it's talking about and what the numbers are.
#
# Dependencies:
#   None - pure Python standard library only.
#   This file can be imported and tested without Shiny or yfinance installed.
import math

# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------

def build_stock_context(
    ticker: str,
    company_name: str,
    start_date: str,
    end_date: str,
    period_return_pct: float,
    ann_vol_pct: float,
    sharpe_ratio: float,
    avg_daily_move_pct: float,
    best_day_pct: float,
    worst_day_pct: float,
    trading_days: int,
) -> str:
    """
    Builds a structured plain-text summary of a stock's metrics.

    This string gets sent to every Claude API call as part of
    the system prompt. It grounds Claude's responses in real numbers
    rather than general knowledge about the stock.

    Parameters
    ----------
    ticker : str
        The stock's exchange symbol. e.g. "NVDA", "AAPL", "TSLA".
        This is the short code used to identify a stock on an exchange.

    company_name : str
        The full company name pulled from yfinance's ticker.info dict.
        e.g. "NVIDIA Corporation". Used to make responses feel more
        natural - Claude can say "NVIDIA" instead of just "NVDA".
        If yfinance couldn't find a name, pass the ticker again as fallback.

    start_date : str
        The start of the selected date range in "YYYY-MM-DD" format.
        e.g. "2024-03-01". Comes from the app's date range input.

    end_date : str
        The end of the selected date range in "YYYY-MM-DD" format.
        e.g. "2025-03-01".

    period_return_pct : float
        How much the stock gained or lost over the entire selected period,
        expressed as a percentage. e.g. 42.3 means +42.3%, -18.5 means a loss.
        Calculated as: ((last_close / first_close) - 1) * 100

    ann_vol_pct : float
        Annualized volatility as a percentage. Measures how much the stock
        typically swings on a daily basis, scaled to a yearly figure.
        e.g. 47.8 means the stock's annualized volatility is 47.8%.
        Calculated as: daily_returns.std() * sqrt(252) * 100

    sharpe_ratio : float
        A measure of risk-adjusted return. How much return the stock
        produced per unit of risk taken. Higher is better.
        e.g. 1.34. Can be negative if returns were below the risk-free rate.
        Pass float('nan') if there wasn't enough data to compute it.

    avg_daily_move_pct : float
        The average daily percentage change over the period.
        e.g. 0.18 means the stock moved +0.18% on an average day.
        Slightly positive even in flat periods due to compounding.

    best_day_pct : float
        The single best daily return in the period, as a percentage.
        e.g. 14.2 means the stock gained 14.2% in one day.

    worst_day_pct : float
        The single worst daily return in the period, as a percentage.
        e.g. -9.6 means the stock fell 9.6% in one day.
        This will always be a negative number (or zero).

    trading_days : int
        The number of trading days (rows) in the dataset.
        Markets are closed on weekends and holidays, so a full calendar
        year typically contains ~252 trading days, not 365.

    Returns
    -------
    str
        A formatted multi-line string. Example output:

            STOCK CONTEXT
            =============
            Ticker:           NVDA (NVIDIA Corporation)
            Period:           2024-03-01 to 2025-03-01 (252 trading days)
            Period return:    +42.3%
            Annualized vol:   47.8%
            Sharpe ratio:     1.34
            Avg daily move:   +0.18%
            Best single day:  +14.2%
            Worst single day: -9.6%

    Notes
    -----
    - All float values are pre-computed by the app before being passed here.
      This function does no math — it only formats.
    - The +/- sign on return values is explicit so Claude can't misread
      a negative number as positive.
    - sharpe_ratio uses a nan-safe formatter so a missing value shows
      as "Insufficient data" rather than "nan" in the prompt.
    """
    # The actual context string.
    
    context = f"""\
        STOCK CONTEXT
        ========================================
        Ticker:             {ticker} ({company_name})
        Period:             {start_date} to {end_date} ({trading_days} trading days)
        Period Return:      {_fmt_pct(period_return_pct)}
        Annualized Vol:     {_fmt_pct(ann_vol_pct)}
        Sharpe Ratio:       {_fmt_sharpe(sharpe_ratio)}
        Avg Daily Move:     {_fmt_pct(avg_daily_move_pct)}
        Best Single Day:    {_fmt_pct(best_day_pct)}
        Worst Single Day:   {_fmt_pct(worst_day_pct)}
    """
    return context

# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------

def _fmt_pct(value: float, suffix:str = "%") -> str:
    '''
    _fmt_pct is a small helper that formats a float as a percentage
    string with an explicit + or - sign and one decimal place.

    Parameters:
    value  — the float to format, e.g. 42.3 or -9.6
    suffix — appended after the number, defaults to "%"

    Examples:
    _fmt_pct(42.3)   → "+42.3%"
    _fmt_pct(-9.6)   → "-9.6%"
    _fmt_pct(0.0)    → "+0.0%"
    '''
    sign = "+" if value >= 0 else "" # Negative values already show a negative sign
    return f"{sign}{value:.1f}{suffix}"

# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------

def _fmt_sharpe(value: float) -> str:
    '''
    _fmt_sharpe handles the case where Sharpe ratio couldn't be computed.
    float('nan') (from the math library) is what you get when you try to 
    divide by zero or when there aren't enough data points. "nan" in a 
    Claude prompt isn't helpful, so it is being replaced with with a 
    fallback string for it to use dictating a data problem.
    '''
    if math.isnan(value):
        return "Insufficient Data"
    return f"{value:.2f}"

