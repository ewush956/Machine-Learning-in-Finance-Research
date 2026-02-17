from shiny import Inputs, Outputs, Session, ui, render, reactive
import pandas as pd
import yfinance as yf

from Tabs.DataTable.datatable import datatable_tab_server
from Tabs.StandardDeviation.tab_stddev import stddev_tab_server

''' ========== Global Server ========== '''
def server(input: Inputs, output: Outputs, session: Session):
# what’s in the text box right now (updates while typing)
    @reactive.calc
    def typed_ticker() -> str:
        return (input.ticker() or "").strip().upper()

    # what the user "committed" by clicking Search (updates only on Search)
    @reactive.calc
    @reactive.event(input.search)
    def searched_ticker() -> str:
        return typed_ticker()

    @reactive.calc
    @reactive.event(input.search)
    def ticker_obj():
        t = searched_ticker()
        return yf.Ticker(t) if t else None

    # metadata: longName / shortName, etc. (one fetch per Search)
    @reactive.calc
    @reactive.event(input.search)
    def ticker_info() -> dict:
        tk = ticker_obj()
        if tk is None:
            return {}
        try:
            return tk.info or {}
        except Exception:
            return {}

    # price history (for only one fetch per Search)
    @reactive.calc
    @reactive.event(input.search)
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