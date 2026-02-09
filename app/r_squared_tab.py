from shiny import ui

def rs_tab():
    return ui.nav_panel(
            "R-squared",
            ui.layout_sidebar(
                ui.sidebar(
                    ui.card(ui.card_header("R-squared Info")),
                    ui.p("test for entry in sidebar"),
                ),
                ui.card(
                    ui.card_header("R-squared Plot"),
                    ui.output_plot("plot_r2")
                ),
            ),
        )