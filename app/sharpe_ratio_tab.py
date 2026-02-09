from shiny import ui

def sr_tab():
    return ui.nav_panel(
            "Sharpe Ratio",
            ui.layout_sidebar(
                ui.sidebar(
                    ui.card(ui.card_header("Sharpe Ratio Info")),
                    ui.p("test for entry in sidebar"),
                ),
                ui.card(
                    ui.card_header("Sharpe Ratio Plot"),
                    ui.output_plot("plot_sharpe")
                ),
            ),
        )