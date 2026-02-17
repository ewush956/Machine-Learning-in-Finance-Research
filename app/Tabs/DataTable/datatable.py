from pathlib import Path
from shiny import ui, render, reactive
import pandas as pd
import yfinance as yf


''' ========== Datatable Tab UI Layout ========== '''
# User Interface Layout Only
def datatable_tab():
    return ui.nav_panel(
        "Data",
        ui.card(
            ui.card_header("Current Loaded Data"),
            ui.output_data_frame("imported_data"),
        ),
    )


''' ========== Datatable Tab Calculations From Server.py Info ========== '''
def datatable_tab_server(input, output, session, prices_df):
    @reactive.calc
    def daily_returns():
        df = prices_df()
        r = df["Close"].pct_change().dropna()
        return r

    @render.text
    def stddev_value():
        return f"Std dev (daily returns): {daily_returns().std():.6f}"