from shiny import ui
from helpers import load_html

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shiny import render

""" ========== Sharpe Ratio Tab UI Layout ========== """


def sharpe_ratio_tab_ui():
    return ui.nav_panel(
        "Sharpe Ratio",
        ui.hr(),
        ui.h5(ui.output_text("sharpe_ratio_tab_ticker_title"), align="center"),
        ui.hr(),
        ui.layout_sidebar(
            ui.sidebar(
                ui.accordion(
                    ui.accordion_panel(
                        "What is it?",
                        load_html(
                            "Markdown/SharpeRatioHTML/1_what_is_sharpe_ratio.html"
                        ),
                    ),
                    ui.accordion_panel(
                        "Interpretation",
                        load_html(
                            "Markdown/SharpeRatioHTML/2_sharpe_interpretation.html"
                        ),
                    ),
                    open=[],
                ),
                width="33rem",
                style="max-height: 90vh; overflow-y: auto;",
                title="About Sharpe Ratio Metrics",
            ),
            ui.accordion(
                ui.accordion_panel(
                    "Risk vs Return (Sharpe Tradeoff View)",
                    ui.output_plot("sharpe_risk_return_scatter_plot"),
                    load_html("Markdown/SharpeRatioHTML/5_risk_return_plot.html"),
                ),
                ui.accordion_panel(
                    "Rolling Sharpe Ratio (How Risk-Adjusted Performance Changes)",
                    ui.output_plot("sharpe_rolling_ratio_plot"),
                    load_html("Markdown/SharpeRatioHTML/4_rolling_sharpe_plot.html"),
                ),
                ui.accordion_panel(
                    "Sharpe Components by Year (Return, Risk, Ratio)",
                    ui.output_plot("sharpe_components_by_year_plot"),
                    load_html(
                        "Markdown/SharpeRatioHTML/3_components_by_year_plot.html"
                    ),
                ),
                style="max-height: 90vh; overflow-y: auto;",
            ),
        ),
    )


def sharpe_ratio_tab_server(
    input, output, session, searched_ticker, ticker_info, history_df
):
    @render.text
    def sharpe_ratio_tab_ticker_title():
        t = searched_ticker()
        info = ticker_info()
        name = info.get("longName") or info.get("shortName")
        return (
            f"{t} — {name}"
            if (t and name)
            else (t or "Enter a ticker and click Search")
        )

    def _get_daily_returns_decimal(df: pd.DataFrame) -> pd.Series:
        if df is None or df.empty or "Close" not in df.columns:
            return pd.Series(dtype=float)
        returns = df["Close"].pct_change().dropna()
        returns.name = "daily_return"
        return returns

    def _daily_risk_free_rate(annual_risk_free_rate: float = 0.02) -> float:
        return (1.0 + annual_risk_free_rate) ** (1.0 / 252.0) - 1.0

    def _annualized_sharpe_ratio(excess_returns: pd.Series) -> float:
        if excess_returns.empty:
            return np.nan
        std = float(excess_returns.std())
        if not np.isfinite(std) or std <= 0:
            return np.nan
        return float(np.sqrt(252.0) * excess_returns.mean() / std)

    @output
    @render.plot(alt="Risk vs Return Scatter with Sharpe Guide")
    def sharpe_risk_return_scatter_plot():
        df = history_df()
        returns = _get_daily_returns_decimal(df)
        rf_daily = _daily_risk_free_rate()
        excess_returns = returns - rf_daily

        fig, ax = plt.subplots(figsize=(10, 6))

        if excess_returns.empty:
            ax.set_title("Risk vs Return (Sharpe Tradeoff View)")
            ax.set_xlabel("Volatility (%)")
            ax.set_ylabel("Excess return (%)")
            ax.text(
                0.5,
                0.5,
                "No return data available.",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            return fig

        window_trading_days = 21
        ann_excess_return_pct = (
            excess_returns.rolling(window=window_trading_days).mean() * 252.0 * 100.0
        )
        ann_volatility_pct = (
            excess_returns.rolling(window=window_trading_days).std()
            * np.sqrt(252.0)
            * 100.0
        )

        valid = ann_excess_return_pct.notna() & ann_volatility_pct.notna()
        x = ann_volatility_pct[valid]
        y = ann_excess_return_pct[valid]

        if x.empty:
            ax.set_title("Risk vs Return (Sharpe Tradeoff View)")
            ax.set_xlabel("Annualized volatility (%)")
            ax.set_ylabel("Annualized excess return (%)")
            ax.text(
                0.5,
                0.5,
                "Not enough data for rolling window.",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            return fig

        ax.scatter(x.values, y.values, s=20, alpha=0.7, label="21-day rolling points")

        overall_sharpe = _annualized_sharpe_ratio(excess_returns)
        if np.isfinite(overall_sharpe):
            x_line = np.linspace(0, float(np.nanmax(x.values) * 1.05), 100)
            y_line = overall_sharpe * x_line
            ax.plot(
                x_line,
                y_line,
                linestyle="--",
                linewidth=1.5,
                label=f"Slope = Sharpe ({overall_sharpe:.2f})",
            )

        ax.axhline(0.0, linestyle=":", linewidth=1)
        ax.set_title("Risk vs Return (Sharpe Tradeoff View)")
        ax.set_xlabel("Annualized volatility (%)")
        ax.set_ylabel("Annualized excess return (%)")
        ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, -0.18),
            ncol=2,
            labelspacing=0.8,
            borderpad=0.7,
            handletextpad=0.9,
            borderaxespad=0.6,
        )
        fig.tight_layout(rect=[0.0, 0.08, 1.0, 1.0])
        return fig

    @output
    @render.plot(alt="Rolling Sharpe Ratio")
    def sharpe_rolling_ratio_plot():
        df = history_df()
        returns = _get_daily_returns_decimal(df)
        rf_daily = _daily_risk_free_rate()
        excess_returns = returns - rf_daily

        fig, ax = plt.subplots(figsize=(10, 6))

        if excess_returns.empty:
            ax.set_title("Rolling Sharpe Ratio (How Risk-Adjusted Performance Changes)")
            ax.set_xlabel("Date")
            ax.set_ylabel("Annualized Sharpe ratio")
            ax.text(
                0.5,
                0.5,
                "No return data available.",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            return fig

        window_trading_days = 63
        rolling_mean = excess_returns.rolling(window=window_trading_days).mean()
        rolling_std = excess_returns.rolling(window=window_trading_days).std()
        rolling_sharpe = np.sqrt(252.0) * (
            rolling_mean / rolling_std.replace(0, np.nan)
        )

        ax.plot(
            rolling_sharpe.index,
            rolling_sharpe.values,
            linewidth=1.5,
            label=f"{window_trading_days}-day rolling Sharpe",
        )
        ax.axhline(0.0, linestyle="--", linewidth=1, label="Break-even (0.0)")
        ax.axhline(1.0, linestyle=":", linewidth=1, label="Strong (1.0)")
        ax.axhline(2.0, linestyle=":", linewidth=1, label="Very strong (2.0)")
        ax.set_title(f"Rolling Sharpe Ratio (Last {window_trading_days} Trading Days)")
        ax.set_xlabel("Date")
        ax.set_ylabel("Annualized Sharpe ratio")
        ax.tick_params(axis="x", labelrotation=35)
        for label in ax.get_xticklabels():
            label.set_ha("right")
        # Add a little data-space padding so the top-right legend overlaps less.
        ax.margins(x=0.03, y=0.14)
        ax.legend(loc="upper right", bbox_to_anchor=(0.98, 0.98), borderaxespad=0.8)
        fig.tight_layout()
        return fig

    @output
    @render.plot(alt="Sharpe Components by Year")
    def sharpe_components_by_year_plot():
        df = history_df()
        returns = _get_daily_returns_decimal(df)
        rf_daily = _daily_risk_free_rate()
        excess_returns = returns - rf_daily

        fig, ax = plt.subplots(figsize=(10, 6))

        if excess_returns.empty:
            ax.set_title("Sharpe Components by Year (Return, Risk, Ratio)")
            ax.set_xlabel("Year")
            ax.set_ylabel("Percent / Sharpe")
            ax.text(
                0.5,
                0.5,
                "No return data available.",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            return fig

        yearly = pd.DataFrame({"excess": excess_returns})
        yearly["year"] = yearly.index.year
        stats = (
            yearly.groupby("year")["excess"]
            .agg(["mean", "std", "count"])
            .rename(columns={"mean": "daily_mean_excess", "std": "daily_volatility"})
        )
        stats = stats[stats["count"] >= 30].copy()

        if stats.empty:
            ax.set_title("Sharpe Components by Year (Return, Risk, Ratio)")
            ax.set_xlabel("Year")
            ax.set_ylabel("Percent / Sharpe")
            ax.text(
                0.5,
                0.5,
                "Not enough data to compute yearly Sharpe components.",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            return fig

        stats["ann_excess_return_pct"] = stats["daily_mean_excess"] * 252.0 * 100.0
        stats["ann_volatility_pct"] = stats["daily_volatility"] * np.sqrt(252.0) * 100.0
        stats["sharpe"] = np.where(
            stats["ann_volatility_pct"] > 0,
            stats["ann_excess_return_pct"] / stats["ann_volatility_pct"],
            np.nan,
        )

        years = stats.index.astype(str)
        x = np.arange(len(stats))
        width = 0.36

        ax.bar(
            x - width / 2,
            stats["ann_excess_return_pct"].values,
            width,
            alpha=0.85,
            label="Annualized Excess return (%)",
        )
        ax.bar(
            x + width / 2,
            stats["ann_volatility_pct"].values,
            width,
            alpha=0.7,
            label="Annualized Volatility (%)",
        )

        ax2 = ax.twinx()
        ax2.plot(
            x,
            stats["sharpe"].values,
            marker="o",
            linewidth=1.8,
            label="Sharpe ratio",
        )

        ax.set_xticks(x)
        ax.set_xticklabels(years)
        ax.set_title("Sharpe Components by Year (Return, Risk, Ratio)")
        ax.set_xlabel("Year")
        ax.set_ylabel("Percent (%)")
        ax2.set_ylabel("Sharpe ratio")

        handles1, labels1 = ax.get_legend_handles_labels()
        handles2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(
            handles1 + handles2,
            labels1 + labels2,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.18),
            ncol=2,
            labelspacing=0.8,
            borderpad=0.7,
            handletextpad=0.9,
            borderaxespad=0.6,
        )
        fig.tight_layout(rect=[0.0, 0.08, 1.0, 1.0])
        return fig
