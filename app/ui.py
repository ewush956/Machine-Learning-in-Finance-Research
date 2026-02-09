from shiny import ui
from data_table_tab import df_tab
from r_squared_tab import rs_tab
from sharpe_ratio_tab import sr_tab
from standard_deviation_tab import sd_tab

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
        df_tab(),
        rs_tab(),
        sr_tab(),
        sd_tab(),
        ui.nav_panel(
            "Beta",
            ui.card(
                ui.card_header("Beta"),
                ui.output_plot("plot_beta"),
            ),
        ),
    ),
)
