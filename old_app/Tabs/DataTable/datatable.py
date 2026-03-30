import pandas as pd
from shiny import ui, render, reactive


''' ========== Datatable Tab UI Layout ========== '''
# User Interface Layout Only
def datatable_tab():
    return ui.nav_panel(
        "Data",
        ui.hr(),
        ui.h5(ui.output_text("data_table_ticker_title"), align="center"),
        ui.hr(),
        ui.navset_tab(
            ui.nav_panel(
                "Table",
                ui.output_data_frame("data_table"), 
            ),
            ui.nav_panel(
                "Summary",
                ui.output_ui("data_summary"),
            ),
        ),
    )


''' ========== Datatable Tab Calculations From Server.py Info ========== '''
def datatable_tab_server(input, output, session, searched_ticker, ticker_info, history_df):

    @reactive.calc
    def table_df() -> pd.DataFrame:
        df = history_df()
        if df.empty:
            return df

        df = df.reset_index()
        df.insert(0, "Row", range(1, len(df) + 1))
        return df

    @render.text
    def data_table_ticker_title():
        t = searched_ticker()
        info = ticker_info()
        name = info.get("longName") or info.get("shortName")
        return f"{t} — {name}" if (t and name) else (t or "Enter a ticker and click Search")

    @render.data_frame
    def data_table():
        return render.DataTable(table_df(), width="100%", height="500px", summary=True)

    @render.ui
    def data_summary():
        df = table_df()
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