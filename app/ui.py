from shiny import ui

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.h2("Dashboard"),
        ui.input_file(
            "research_pdf",
            "Upload PDF",
            accept=[".pdf"],
        ),
    ),
    ui.card(
        ui.card_header("Workspace"),
        ui.p(""),
    ),
)
