from shiny import ui
from helpers import load_html

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shiny import render

""" ========== Standard Deviation Tab UI Layout ========== """


def stddev_tab_ui():
    return ui.nav_panel(
        "Standard Deviation",
        ui.layout_sidebar(
            ui.sidebar(
                ui.accordion(
                    ui.accordion_panel(
                        "What is it?",
                        load_html("Markdown/StandardDeviationHTML/1_what_is_sd.html"),
                    ),
                    ui.accordion_panel(
                        "Interpretation",
                        load_html(
                            "Markdown/StandardDeviationHTML/2_sd_interpretation.html"
                        ),
                    ),
                    open=[],
                ),
                width="33rem",
                style="max-height: 80vh; overflow-y: auto;",
            ),
            ui.div(
                ui.card(
                    ui.card_header("Daily Returns with Standard Deviation Band"),
                    ui.output_plot("stddev_returns_band_plot"),
                    load_html(
                        "Markdown/StandardDeviationHTML/3_returns_band_plot.html"
                    ),
                ),
                ui.card(
                    ui.card_header(
                        "Return Distribution (How Often Each Daily Change Happens)"
                    ),
                    ui.output_plot("stddev_returns_distribution_plot"),
                    load_html(
                        "Markdown/StandardDeviationHTML/4_returns_dist_plot.html"
                    ),
                ),
                ui.card(
                    ui.card_header("Rolling Volatility (How Risk Changes Over Time)"),
                    ui.output_plot("stddev_rolling_volatility_plot"),
                    load_html(
                        "Markdown/StandardDeviationHTML/5_rolling_volatility_plot.html"
                    ),
                ),
                style="display: grid; gap: 1rem;",
            ),
        ),
    )


def stddev_tab_server(input, output, session, searched_ticker, ticker_info, history_df):
    def _get_daily_returns_percent(df: pd.DataFrame) -> pd.Series:
        if df is None or df.empty or "Close" not in df.columns:
            return pd.Series(dtype=float)
        returns = df["Close"].pct_change().dropna() * 100.0
        returns.name = "daily_return_pct"
        return returns

    def _normal_pdf(x: np.ndarray, mean: float, std: float) -> np.ndarray:
        if std <= 0 or not np.isfinite(std):
            return np.zeros_like(x, dtype=float)
        z = (x - mean) / std
        return (1.0 / (std * np.sqrt(2.0 * np.pi))) * np.exp(-0.5 * z * z)

    @output
    @render.plot(alt="Daily Returns with Standard Deviation Band")
    def stddev_returns_band_plot():
        df = history_df()
        returns = _get_daily_returns_percent(df)
        fig, ax = plt.subplots(figsize=(10, 4))

        if returns.empty:
            ax.set_title("Daily Returns with Standard Deviation Band")
            ax.set_xlabel("Date")
            ax.set_ylabel("Daily Return (%)")
            ax.text(
                0.5,
                0.5,
                "No return data available.",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            return fig

        mean = float(returns.mean())
        std = float(returns.std())
        dates = returns.index

        ax.plot(dates, returns, linewidth=1, label="Daily price change (%)")
        ax.axhline(
            mean,
            linestyle="--",
            linewidth=1.5,
            label=f"Average daily change ({mean:.2f}%)",
        )

        if np.isfinite(std) and std > 0:
            ax.fill_between(
                dates,
                mean - std,
                mean + std,
                alpha=0.25,
                label=f"Typical range (±1σ = {std:.2f}%)",
            )
            ax.axhline(mean + std, linestyle=":", linewidth=1)
            ax.axhline(mean - std, linestyle=":", linewidth=1)

        ax.set_title("Daily Returns with Standard Deviation Band")
        ax.set_xlabel("Date")
        ax.set_ylabel("Daily Return (%)")
        ax.legend(loc="upper right")
        fig.tight_layout()
        return fig

    @output
    @render.plot(alt="Return Distribution Histogram with Normal Overlay")
    def stddev_returns_distribution_plot():
        df = history_df()
        returns = _get_daily_returns_percent(df)

        fig, ax = plt.subplots(figsize=(10, 4))

        if returns.empty:
            ax.set_title("Return Distribution (How Often Each Daily Change Happens)")
            ax.set_xlabel("Daily Return (%)")
            ax.set_ylabel("Number of days")
            ax.text(
                0.5,
                0.5,
                "No return data available.",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            return fig

        mean = float(returns.mean())
        std = float(returns.std())

        counts, bin_edges, _ = ax.hist(
            returns.values,
            bins=40,
            density=False,
            alpha=0.85,
            label="Real daily changes (count)",
        )

        if np.isfinite(std) and std > 0:
            x = np.linspace(bin_edges[0], bin_edges[-1], 300)
            pdf = _normal_pdf(x, mean, std)

            bin_width = float(bin_edges[1] - bin_edges[0])
            scaled_pdf = pdf * len(returns) * bin_width

            ax.plot(
                x,
                scaled_pdf,
                linewidth=2,
                label="Ideal bell curve",
            )
            ax.axvline(
                mean, linestyle="--", linewidth=1.5, label=f"Average ({mean:.2f}%)"
            )
            ax.axvline(mean + std, linestyle=":", linewidth=1, label="±1σ")
            ax.axvline(mean - std, linestyle=":", linewidth=1)

        ax.set_title("Return Distribution (How Often Each Daily Change Happens)")
        ax.set_xlabel("Daily Return (%)")
        ax.set_ylabel("Number of days")
        ax.legend(loc="upper right")
        fig.tight_layout()
        return fig

    @output
    @render.plot(alt="Rolling Volatility Plot")
    def stddev_rolling_volatility_plot():
        df = history_df()
        returns = _get_daily_returns_percent(df)

        fig, ax = plt.subplots(figsize=(10, 4))

        if returns.empty:
            ax.set_title("Rolling Volatility (How Risk Changes Over Time)")
            ax.set_xlabel("Date")
            ax.set_ylabel("Typical daily swing (%)")
            ax.text(
                0.5,
                0.5,
                "No return data available.",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            return fig

        window_trading_days = 20
        rolling_vol = returns.rolling(window=window_trading_days).std()

        ax.plot(
            rolling_vol.index,
            rolling_vol.values,
            linewidth=1.5,
            label="Typical daily swing (rolling σ)",
        )
        ax.set_title(
            f"Rolling Volatility (Typical Daily Swing, Last {window_trading_days} Trading Days)"
        )
        ax.set_xlabel("Date")
        ax.set_ylabel("Typical daily swing (%)")
        ax.legend(loc="upper right")
        fig.tight_layout()
        return fig
