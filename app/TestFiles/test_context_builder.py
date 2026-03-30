# TestFiles/test_context_builder.py
#
# Purpose:
#   Verifies that build_stock_context() produces correctly formatted
#   output across a range of realistic inputs.
#
# How to run:
#   From your project root directory in the terminal:
#       python -m pytest ./app/TestFiles/test_context_builder.py -v
#
#   Or without pytest, just run it directly:
#       python ./app/TestFiles/test_context_builder.py
#
# What we're asserting:
#   1. Normal positive-return stock -> correct labels and sign
#   2. Negative-return stock -> loss language and minus sign
#   3. Zero return -> shows as +0.0% (edge case)
#   4. NaN Sharpe ratio -> shows "Insufficient data", not "nan"
#   5. All expected keys appear in output (structural check)
#   6. Trading days appears in output
#   7. Company name appears alongside ticker


import sys
import os
import math
from context_builder import build_stock_context


# Shared Tester Values --------------------------------------------------------
NVDA_KWARGS_1 = dict(
    ticker="NVDA",
    company_name="NVIDIA Corporation",
    start_date="2024-03-01",
    end_date="2025-03-01",
    period_return_pct=42.3,
    ann_vol_pct=47.8,
    sharpe_ratio=1.34,
    avg_daily_move_pct=0.18,
    best_day_pct=14.2,
    worst_day_pct=-9.6,
    trading_days=252,
)

NVDA_KWARGS_2 = dict(
    ticker="NVDA",
    company_name="NVIDIA Corporation",
    start_date="2024-03-01",
    end_date="2025-03-01",
    period_return_pct=-42.3,
    ann_vol_pct=47.8,
    sharpe_ratio=math.nan,
    avg_daily_move_pct=0.18,
    best_day_pct=14.2,
    worst_day_pct=-9.6,
    trading_days=252,
)

# -Tests Values ---------------------------------------------------------------
def test_ticker_and_company_appear():
    """
    The ticker symbol and company name must both appear in the output.
    Claude needs both — it uses the company name for natural language
    but the ticker is the ground truth identifier.
    """
    result = build_stock_context(**NVDA_KWARGS_1)
    assert "NVDA" in result
    assert "NVIDIA Corporation" in result


def test_positive_return_has_plus_sign():
    """
    A positive period return must be prefixed with "+".
    Without the explicit sign, Claude might misread "+42.3%"
    as ambiguous. We always want the sign to be unambiguous.
    """
    result = build_stock_context(**NVDA_KWARGS_1)
    assert "+42.3%" in result


def test_negative_return_has_minus_sign():
    """
    A loss should show with a minus sign and no plus prefix.
    """
    kwargs = {**NVDA_KWARGS_1, "period_return_pct": -18.5}
    result = build_stock_context(**kwargs)
    assert "-18.5%" in result
    assert "+-18.5%" not in result  # make sure we're not doubling up signs


def test_zero_return_shows_as_positive():
    """
    Zero return is technically non-negative, so it should show as +0.0%.
    This is an edge case that's easy to get wrong with sign logic.
    """
    kwargs = {**NVDA_KWARGS_1, "period_return_pct": 0.0}
    result = build_stock_context(**kwargs)
    assert "+0.0%" in result


def test_nan_sharpe_shows_insufficient_data():
    """
    When Sharpe ratio can't be computed (e.g. a brand new stock with
    only a few days of data), float('nan') is passed in.
    The output must NOT contain the string "nan" — that's meaningless
    to a beginner. It should say "Insufficient data" instead.
    """
    kwargs = {**NVDA_KWARGS_1, "sharpe_ratio": float("nan")}
    result = build_stock_context(**kwargs)
    assert "Insufficient Data" in result
    assert "nan" not in result.lower()


def test_trading_days_appear():
    """
    The trading day count must appear so Claude can reason about
    how long the period is. "252 trading days" vs "5 trading days"
    changes how Claude should interpret the numbers.
    """
    result = build_stock_context(**NVDA_KWARGS_1)
    assert "252" in result


def test_worst_day_is_negative():
    """
    Worst day should always be zero or negative. This test both checks
    the formatting and acts as a sanity check that we haven't accidentally
    flipped the sign when pulling the value from the DataFrame.
    """
    result = build_stock_context(**NVDA_KWARGS_1)
    assert "-9.6%" in result


def test_best_day_is_positive():
    """
    Best day should always be zero or positive.
    """
    result = build_stock_context(**NVDA_KWARGS_1)
    assert "+14.2%" in result


def test_date_range_appears():
    """
    Both start and end dates must appear so Claude can contextualise
    whether the period covers a bull run, a crash, or a sideways market.
    """
    result = build_stock_context(**NVDA_KWARGS_1)
    assert "2024-03-01" in result
    assert "2025-03-01" in result


def test_output_is_string():
    """
    Basic type check. The rest of the app assumes this function
    returns a str. If it ever returns None or a dict, things will
    break silently downstream.
    """
    result = build_stock_context(**NVDA_KWARGS_1)
    assert isinstance(result, str)


def test_output_is_non_empty():
    """
    Guard against accidentally returning an empty string,
    which would give Claude no context at all.
    """
    result = build_stock_context(**NVDA_KWARGS_1)
    assert len(result.strip()) > 0
    
    
# Manual runner ---------------------------------------------------------------
# This block only runs when you execute this file directly:
#   python TestFiles/test_context_builder.py
#
# It won't run when pytest collects and runs the file.
# This gives you a quick way to visually inspect the output
# without needing pytest installed.
if __name__ == "__main__":
    print("\n=== Visual Output Check ===\n")
    print(build_stock_context(**NVDA_KWARGS_1))
    
    print("\n=== NaN Sharpe variant ===\n")
    print(build_stock_context(**NVDA_KWARGS_2))
    
    print("\n=== Negative return variant ===\n")
    print(build_stock_context(**NVDA_KWARGS_2))
    
    print("\nRunning assertions manually...")
    tests = [
        test_ticker_and_company_appear,
        test_positive_return_has_plus_sign,
        test_negative_return_has_minus_sign,
        test_zero_return_shows_as_positive,
        test_nan_sharpe_shows_insufficient_data,
        test_trading_days_appear,
        test_worst_day_is_negative,
        test_best_day_is_positive,
        test_date_range_appears,
        test_output_is_string,
        test_output_is_non_empty,
    ]
    for t in tests:
        try:
            t()
            print(f"✅ {t.__name__}")
        except AssertionError as e:
            print(f"❌ {t.__name__} — {e}")
    