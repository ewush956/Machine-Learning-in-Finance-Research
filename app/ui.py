from shiny import ui

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.h2("Stuff!"),
        ui.help_text(
            "Could probably have some different options here for different data or visualizations"
        ),
        ui.input_select(
            "concept",
            "Setting",
            [
                "Heat Map",
                "Cold Map",
                "Luke Warm Map",
                "Histogram... Map?",
            ],
        ),
        ui.help_text("Could allow for uploading CSV data instead of API"),
        ui.input_file(
            "csv_upload",
            "Upload CSV",
            accept=[".csv"],
        ),
    ),
    ui.help_text(
        "Right now these won't load anything because we have no graphs, i'll maybe set up set temp images or something to adjust the layout"
    ),
    ui.navset_card_tab(
        ui.nav_panel(
            "Data Table",
            ui.card(
                ui.card_header("Current Data"),
                ui.output_data_frame("imported_data"),
            ),
        ),
        ui.nav_panel(
            "R-squared",
            ui.card(
                ui.card_header("R-squared"),
                ui.output_plot("plot_r2"),
            ),
        ),
        ui.nav_panel(
            "Sharpe Ratio",
            ui.card(
                ui.card_header("Sharpe Ratio"),
                ui.output_plot("plot_sharpe"),
            ),
        ),
        ui.nav_panel(
            "Standard Deviation",
            ui.card(
                ui.card_header("Standard Deviation"),
                ui.output_plot("plot_stddev"),
            ),
        ),
        ui.nav_panel(
            "Beta",
            ui.card(
                ui.card_header("Beta"),
                ui.output_plot("plot_beta"),
            ),
        ),
    ),
)
