from plot_theme import apply_matplotlib_theme
from shiny import Inputs, Outputs, Session, reactive
import pandas as pd
import yfinance as yf

from Tabs.DataTable.datatable import datatable_tab_server
from Tabs.StandardDeviation.tab_stddev import stddev_tab_server
from Tabs.SharpeRatio.tab_sharpe_ratio import sharpe_ratio_tab_server
from llm_panel import llm_panel_server

''' ========== Global Server ========== '''
def server(input: Inputs, output: Outputs, session: Session):
    default_ticker = "NVDA"
    searched_ticker_state = reactive.value(default_ticker)

    @reactive.effect
    @reactive.event(input.search)
    def _update_searched_ticker():
        typed = (input.ticker() or "").strip().upper()
        searched_ticker_state.set(typed or default_ticker)

    @reactive.calc
    def searched_ticker() -> str:
        return searched_ticker_state()

    @reactive.calc
    def ticker_obj():
        t = searched_ticker()
        return yf.Ticker(t) if t else None

    # metadata: longName / shortName, etc. (one fetch per Search)
    @reactive.calc
    def ticker_info() -> dict:
        tk = ticker_obj()
        if tk is None:
            return {}
        try:
            return tk.info or {}
        except Exception:
            return {}

    # sync matplotlib theme.
    @reactive.effect
    def _sync_matplotlib_theme():
        apply_matplotlib_theme(input.color_mode())

    # price history (for only one fetch per Search)
    @reactive.calc
    def history_df() -> pd.DataFrame:
        tk = ticker_obj()
        if tk is None:
            return pd.DataFrame()
        start, end = input.dates()
        return tk.history(start=start, end=end)  # raw df (the index is the Date)

    # Pass shared reactives to tabs
    datatable_tab_server(
        input, output, session,
        searched_ticker=searched_ticker,
        ticker_info=ticker_info,
        history_df=history_df,
    )
    stddev_tab_server(
        input, output, session,
        searched_ticker=searched_ticker,
        ticker_info=ticker_info,
        history_df=history_df,
    )
    sharpe_ratio_tab_server(
        input, output, session,
        searched_ticker=searched_ticker,
        ticker_info=ticker_info,
        history_df=history_df,
    )
    llm_panel_server(
        input, output, session,
        searched_ticker=searched_ticker,
        ticker_info=ticker_info,
        history_df=history_df,
    )
