# TestFiles/test_llm_panel.py
#
# How to run:
#   python -m pytest ./app/TestFiles/test_llm_panel.py -v
#   python ./app/TestFiles/test_llm_panel.py
#
# What we test:
#   - _compute_metrics() with a realistic DataFrame
#   - _compute_metrics() fallback with empty/invalid input
#   - Constants are sane values
#   - SYSTEM_PROMPT contains required guardrails
#   - _call_llm() can be mocked cleanly
#   - build_stock_context() integrates correctly with _compute_metrics() output
#
# What we do NOT test here:
#   - Shiny reactive functions (llm_panel_server, render functions)
#     These require a running Shiny session to execute. They are covered
#     by manual integration testing when you run the app.

import sys
import os
import math
from unittest.mock import patch, MagicMock

import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from llm_panel import (
    _compute_metrics,
    _call_llm,
    MAX_CALLS_PER_SESSION,
    LLM_MODEL,
    MAX_TOKENS,
    SYSTEM_PROMPT,
)
from context_builder import build_stock_context


# Shared Values ---------------------------------------------------------------

def _make_realistic_df(n_days: int = 252, seed: int = 42) -> pd.DataFrame:
    """
    Builds a realistic-looking stock price DataFrame for testing.

    Uses a geometric random walk — the same statistical model that
    underpins the Black-Scholes options pricing formula. Each day's
    return is drawn from a normal distribution, then compounded.

    Parameters
    ----------
    n_days : int
        Number of trading days to simulate. Default 252 = 1 year.
    seed : int
        Random seed for reproducibility. Same seed = same prices every run.

    Returns
    -------
    pd.DataFrame
        DataFrame with a DatetimeIndex and a "Close" column,
        exactly matching the structure of a yfinance history_df().
    """
    np.random.seed(seed)
    # daily_returns: small positive drift (0.001 = ~25% annual) with
    # realistic volatility (0.02 = ~2% daily = ~32% annualized)
    daily_returns = np.random.normal(loc=0.001, scale=0.02, size=n_days)
    # Start at $100, compound each day's return
    prices = 100.0 * np.exp(np.cumsum(daily_returns))
    dates = pd.bdate_range("2024-01-01", periods=n_days)
    return pd.DataFrame({"Close": prices}, index=dates)


SAMPLE_DF = _make_realistic_df()
SAMPLE_TICKER = "TEST"
SAMPLE_COMPANY = "Test Corporation"
SAMPLE_START = "2024-01-01"
SAMPLE_END = "2024-12-31"


# Constants tests ---------------------------------------------------------------

def test_max_calls_is_positive_integer():
    """Session limit must be a positive integer. Zero or negative would
    disable the panel immediately on load."""
    assert isinstance(MAX_CALLS_PER_SESSION, int)
    assert MAX_CALLS_PER_SESSION > 0


def test_max_tokens_is_positive_integer():
    """MAX_TOKENS must be a positive integer — the API will reject 0 or negative."""
    assert isinstance(MAX_TOKENS, int)
    assert MAX_TOKENS > 0


def test_llm_model_is_string():
    """Model name must be a non-empty string."""
    assert isinstance(LLM_MODEL, str)
    assert len(LLM_MODEL) > 0


def test_system_prompt_contains_no_advice_guardrail():
    """
    The system prompt must explicitly tell Claude not to give buy/sell advice.
    This is the most important guardrail in the whole file — if it's missing,
    Claude might act as a financial advisor, which it is not.
    """
    assert "buy" in SYSTEM_PROMPT.lower() or "advice" in SYSTEM_PROMPT.lower()


def test_system_prompt_mentions_plain_english():
    """Claude must be instructed to use plain language for beginners."""
    assert "plain" in SYSTEM_PROMPT.lower() or "jargon" in SYSTEM_PROMPT.lower()


#  _compute_metrics() tests ---------------------------------------------------------------

def test_compute_metrics_returns_dict():
    result = _compute_metrics(SAMPLE_DF, SAMPLE_TICKER, SAMPLE_COMPANY, SAMPLE_START, SAMPLE_END)
    assert isinstance(result, dict)


def test_compute_metrics_has_all_required_keys():
    """
    The returned dict must contain exactly the keys that build_stock_context()
    expects. If any key is missing, the **unpacking call will raise a TypeError.
    """
    result = _compute_metrics(SAMPLE_DF, SAMPLE_TICKER, SAMPLE_COMPANY, SAMPLE_START, SAMPLE_END)
    required_keys = {
        "ticker", "company_name", "start_date", "end_date",
        "period_return_pct", "ann_vol_pct", "sharpe_ratio",
        "avg_daily_move_pct", "best_day_pct", "worst_day_pct",
        "trading_days",
    }
    assert required_keys.issubset(result.keys())


def test_compute_metrics_trading_days_correct():
    """Trading days should match the number of rows in the DataFrame."""
    result = _compute_metrics(SAMPLE_DF, SAMPLE_TICKER, SAMPLE_COMPANY, SAMPLE_START, SAMPLE_END)
    assert result["trading_days"] == len(SAMPLE_DF)


def test_compute_metrics_worst_day_is_negative_or_zero():
    """Worst day is the minimum return — should always be ≤ 0 in a realistic series."""
    result = _compute_metrics(SAMPLE_DF, SAMPLE_TICKER, SAMPLE_COMPANY, SAMPLE_START, SAMPLE_END)
    assert result["worst_day_pct"] <= 0


def test_compute_metrics_best_day_is_positive_or_zero():
    """Best day should always be ≥ 0."""
    result = _compute_metrics(SAMPLE_DF, SAMPLE_TICKER, SAMPLE_COMPANY, SAMPLE_START, SAMPLE_END)
    assert result["best_day_pct"] >= 0


def test_compute_metrics_best_greater_than_worst():
    """Best day must always be greater than or equal to worst day."""
    result = _compute_metrics(SAMPLE_DF, SAMPLE_TICKER, SAMPLE_COMPANY, SAMPLE_START, SAMPLE_END)
    assert result["best_day_pct"] >= result["worst_day_pct"]


def test_compute_metrics_ann_vol_is_positive():
    """Annualized volatility must be strictly positive for any non-flat series."""
    result = _compute_metrics(SAMPLE_DF, SAMPLE_TICKER, SAMPLE_COMPANY, SAMPLE_START, SAMPLE_END)
    assert result["ann_vol_pct"] > 0


def test_compute_metrics_sharpe_is_finite_for_good_data():
    """For a realistic price series, Sharpe should be a finite float."""
    result = _compute_metrics(SAMPLE_DF, SAMPLE_TICKER, SAMPLE_COMPANY, SAMPLE_START, SAMPLE_END)
    assert math.isfinite(result["sharpe_ratio"])


def test_compute_metrics_ticker_passthrough():
    """Ticker and company name should pass through unchanged."""
    result = _compute_metrics(SAMPLE_DF, "AAPL", "Apple Inc.", SAMPLE_START, SAMPLE_END)
    assert result["ticker"] == "AAPL"
    assert result["company_name"] == "Apple Inc."


def test_compute_metrics_empty_df_returns_fallback():
    """
    An empty DataFrame should return the fallback dict with safe zero values,
    not raise an exception. This covers the case where the user hasn't
    searched a ticker yet.
    """
    result = _compute_metrics(pd.DataFrame(), SAMPLE_TICKER, SAMPLE_COMPANY, SAMPLE_START, SAMPLE_END)
    assert result["trading_days"] == 0
    assert result["period_return_pct"] == 0.0
    assert math.isnan(result["sharpe_ratio"])


def test_compute_metrics_missing_close_column_returns_fallback():
    """DataFrame without a Close column should return fallback, not KeyError."""
    bad_df = pd.DataFrame({"Open": [100, 101, 102]})
    result = _compute_metrics(bad_df, SAMPLE_TICKER, SAMPLE_COMPANY, SAMPLE_START, SAMPLE_END)
    assert result["trading_days"] == 0


def test_compute_metrics_single_row_returns_fallback():
    """
    A single-row DataFrame can't compute returns (no previous day exists).
    Should return fallback rather than NaN-filled results.
    """
    single_row = SAMPLE_DF.iloc[:1].copy()
    result = _compute_metrics(single_row, SAMPLE_TICKER, SAMPLE_COMPANY, SAMPLE_START, SAMPLE_END)
    assert result["trading_days"] == 0


#  Integration test: _compute_metrics + build_stock_context ---------------------------------------------------------------

def test_metrics_to_context_integration():
    """
    The output of _compute_metrics() should feed into build_stock_context()
    without any errors when unpacked with **. This is the exact call pattern
    used in _build_full_system_prompt().
    """
    metrics = _compute_metrics(SAMPLE_DF, SAMPLE_TICKER, SAMPLE_COMPANY, SAMPLE_START, SAMPLE_END)
    context = build_stock_context(**metrics)
    assert isinstance(context, str)
    assert len(context.strip()) > 0
    assert SAMPLE_TICKER in context


# _call_llm() mock test ---------------------------------------------------------------

def test_call_llm_returns_response_text():
    """
    _call_llm() should return the .text of the first content block.
    We mock the anthropic client so no real API call is made.
    This test verifies our function correctly extracts the text from
    the response structure — if Anthropic changes their SDK response
    format, this test will catch it.

    unittest.mock.patch temporarily replaces "anthropic.Anthropic" with
    a MagicMock object for the duration of this test only.
    MagicMock automatically creates fake attributes and methods on demand.
    """
    mock_response_text = "This is a mocked assistant response."

    with patch("llm_panel.anthropic") as mock_anthropic_module:
        # Build the fake response structure that mirrors the real SDK:
        # response.content[0].text
        mock_content_block = MagicMock()
        mock_content_block.text = mock_response_text

        mock_response = MagicMock()
        mock_response.content = [mock_content_block]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_module.Anthropic.return_value = mock_client

        result = _call_llm(
            system="You are a test assistant.",
            messages=[{"role": "user", "content": "Hello"}],
        )

    assert result == mock_response_text


def test_call_llm_passes_correct_model():
    """
    Verify that _call_llm() uses the LLM_MODEL constant when calling
    the API — not a hardcoded string that might get out of sync.
    """
    with patch("llm_panel.anthropic") as mock_anthropic_module:
        mock_content_block = MagicMock()
        mock_content_block.text = "response"
        mock_response = MagicMock()
        mock_response.content = [mock_content_block]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_module.Anthropic.return_value = mock_client

        _call_llm("system", [{"role": "user", "content": "hi"}])

        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == LLM_MODEL
        assert call_kwargs["max_tokens"] == MAX_TOKENS


#  Manual runner ---------------------------------------------------------------

if __name__ == "__main__":
    print("=== _compute_metrics visual check ===\n")
    metrics = _compute_metrics(SAMPLE_DF, "DEMO", "Demo Corporation", "2024-01-01", "2024-12-31")
    for k, v in metrics.items():
        print(f"  {k}: {v}")

    print("\n=== context integration check ===\n")
    print(build_stock_context(**metrics))

    print("\nRunning assertions manually...")
    tests = [
        test_max_calls_is_positive_integer,
        test_max_tokens_is_positive_integer,
        test_llm_model_is_string,
        test_system_prompt_contains_no_advice_guardrail,
        test_system_prompt_mentions_plain_english,
        test_compute_metrics_returns_dict,
        test_compute_metrics_has_all_required_keys,
        test_compute_metrics_trading_days_correct,
        test_compute_metrics_worst_day_is_negative_or_zero,
        test_compute_metrics_best_day_is_positive_or_zero,
        test_compute_metrics_best_greater_than_worst,
        test_compute_metrics_ann_vol_is_positive,
        test_compute_metrics_sharpe_is_finite_for_good_data,
        test_compute_metrics_ticker_passthrough,
        test_compute_metrics_empty_df_returns_fallback,
        test_compute_metrics_missing_close_column_returns_fallback,
        test_compute_metrics_single_row_returns_fallback,
        test_metrics_to_context_integration,
        test_call_llm_returns_response_text,
        test_call_llm_passes_correct_model,
    ]
    for t in tests:
        try:
            t()
            print(f"  ✓ {t.__name__}")
        except AssertionError as e:
            print(f"  ✗ {t.__name__} — {e}")
