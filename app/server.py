from shiny import Inputs, Outputs, Session, ui, render, reactive
import pandas as pd
import yfinance as yf

from Tabs.DataTable.datatable import datatable_tab_server
from Tabs.StandardDeviation.tab_stddev import stddev_tab_server

''' ========== Global Server ========== '''
def server(input: Inputs, output: Outputs, session: Session):
    @reactive.calc
    def prices_df() -> pd.DataFrame:
        ticker = input.ticker()          # must match UI id
        start, end = input.dates()       # must match UI id

        df = yf.Ticker(ticker).history(start=start, end=end)
        df = df.reset_index()            # show Date column

        df.insert(0, "Row", range(1, len(df) + 1))
        return df

    @render.data_frame
    def imported_data():
        return render.DataTable(
            prices_df(),
            width="100%",
            height="750px",
            summary=True
        )

    datatable_tab_server(input, output, session, prices_df=prices_df)
    stddev_tab_server(input, output, session, prices_df=prices_df)