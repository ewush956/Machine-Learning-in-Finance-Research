from shiny import ui

def df_tab():
    return ui.nav_panel(
        "Data Table",
        ui.card(
            ui.card_header("Current Data"),
            ui.output_data_frame("imported_data"),
        ),
    )