from pathlib import Path
from shiny import ui, render
from helpers import load_html

''' ========== Standard Deviation Tab UI Layout ========== '''
# User Interface Layout Only
def stddev_tab_ui():
    return ui.nav_panel(
        "Standard Deviation",
        ui.layout_sidebar(
            ui.sidebar(
                ui.accordion(
                    ui.accordion_panel("What is it?", load_html("app/Markdown/StandardDeviationHTML/1_what_is_sd.html")),
                    ui.accordion_panel("Interpretation", load_html("app/Markdown/StandardDeviationHTML/2_sd_interpretation.html")),
                    open=[]
                ),
                width="33rem",
                style="max-height: 80vh; overflow-y: auto;"
            ),
            ui.card(
                ui.card_header("Current Data Results"),
                ui.output_plot("stdev_plot")
            ),
        ),
    )


''' ========== Standard Deviation Specific Server Functions ========== '''
# Use for plotting, calculations, etc.
def stddev_tab_server(input, output, session, data_path: Path):
    @render.plot(alt="Standard Deviation Tab Data Plot")
    def stdev_plot():
        pass

