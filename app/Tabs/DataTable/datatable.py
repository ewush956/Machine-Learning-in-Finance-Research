import pandas as pd
from shiny import ui, render, reactive
from shinywidgets import output_widget, render_widget
import plotly.graph_objects as go


''' ========== Datatable Tab UI Layout ========== '''
# User Interface Layout Only
def datatable_tab():
    return ui.nav_panel(
        "Data",
        ui.page_navbar(
            ui.nav_panel(
                "Table",
                ui.output_data_frame("data_table"),
            ),
            ui.nav_panel(
                "Candlestick",
                output_widget("data_candles"),
            ),
            ui.nav_panel(
                "Summary",
                ui.output_ui("data_summary"),
            ),
        ),
    )


''' ========== Datatable Tab Calculations From Server.py Info ========== '''
def datatable_tab_server(input, output, session, prices_df):
    
    @render.data_frame
    def data_table():
        df = prices_df()
        return render.DataTable(df, width="100%", height="500px", summary=True)
    
    @render_widget
    def data_candles():
        df = prices_df()

        # Make sure Date is a column
        if "Date" not in df.columns:
            df = df.reset_index()

        fig = go.Figure(
            data=[
                go.Candlestick(
                    x=df["Date"],
                    open=df["Open"],
                    high=df["High"],
                    low=df["Low"],
                    close=df["Close"],
                    name=input.ticker(),  # uses your global sidebar input
                )
            ]
        )

        # SMA(20)
        sma = df["Close"].rolling(window=20).mean()
        fig.add_scatter(
            x=df["Date"],
            y=sma,
            mode="lines",
            name="SMA (20)",
        )

        fig.update_layout(
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="top", y=1, xanchor="right", x=1),
        )
        return fig

    @render.ui
    def data_summary():
        df = prices_df()
        close = df["Close"]
        last_close = float(close.iloc[-1])
        period_return = float(close.iloc[-1] / close.iloc[0] - 1)

        # daily returns + annualized vol (rough but common)
        rets = close.pct_change().dropna()
        ann_vol = float(rets.std() * (252 ** 0.5))

        return ui.div(
            ui.h4("Quick stats"),
            ui.tags.ul(
                ui.tags.li(f"Last close: {last_close:,.2f}"),
                ui.tags.li(f"Period return: {period_return:.2%}"),
                ui.tags.li(f"Annualized volatility (from daily returns): {ann_vol:.2%}"),
                ui.tags.li(f"Rows (trading days): {len(df)}"),
            ),
        )