import pandas as pd
from shiny import ui, render, reactive


''' ========== Datatable Tab UI Layout ========== '''
# User Interface Layout Only
def datatable_tab_ui():
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
