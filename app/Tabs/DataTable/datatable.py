from pathlib import Path
from shiny import ui, render
import pandas as pd


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


''' ========== Datatable Specific Server Functions ========== '''
# Use for plotting, calculations, etc.
def datatable_tab_server(input, output, session, data_path: Path):
    @render.data_frame
    def imported_data():
        df = pd.read_excel(data_path).copy()
        df.insert(0, "Row", (df.index + 1))
        return render.DataTable(df,
                                width='100%',
                                height='500px',
                                summary=True
                                )