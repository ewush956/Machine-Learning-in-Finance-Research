# ########################################################
# #                      Imports                         #
# ########################################################
from plot_theme import apply_matplotlib_theme
from shiny import Inputs, Outputs, Session, reactive
from Tabs.DataTable.datatable import datatable_tab_server
from Tabs.StandardDeviation.tab_stddev import stddev_tab_server
from Tabs.SharpeRatio.tab_sharpe_ratio import sharpe_ratio_tab_server
from llm_panel import llm_panel_server

import pandas as pd
import yfinance as yf


# ####################################################################
# #                      Main Server for App                         #
# ####################################################################
def server(input: Inputs, output: Outputs, session: Session):
    default_ticker = ""
    searched_ticker_state = reactive.value(default_ticker)
    graph_color_mode_trigger = reactive.value(0)

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
    @reactive.event(input.color_mode)
    def _sync_matplotlib_theme():
        print("[theme] effect fired")
        mode = input.color_mode()
        print(f"[theme] switching to: {mode}, trigger count: {graph_color_mode_trigger()}")
        apply_matplotlib_theme(input.color_mode())
        graph_color_mode_trigger.set(graph_color_mode_trigger() + 1)


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
        graph_color_mode_trigger=graph_color_mode_trigger
    )
    sharpe_ratio_tab_server(
        input, output, session,
        searched_ticker=searched_ticker,
        ticker_info=ticker_info,
        history_df=history_df,
        graph_color_mode_trigger=graph_color_mode_trigger
    )
    llm_panel_server(
        input, output, session,
        searched_ticker=searched_ticker,
        ticker_info=ticker_info,
        history_df=history_df
    )
