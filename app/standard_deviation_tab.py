from pathlib import Path
from shiny import ui

# Load the file content once at the top
# Assuming your file is in a folder named 'content'
test_html_path = Path("Markdown/test.html")

try:
    with open(test_html_path, "r", encoding="utf-8") as f:
        # Wrap the raw text in ui.HTML so Shiny treats it as code, not plain text
        standard_dev_content = ui.HTML(f.read())
except FileNotFoundError:
    standard_dev_content = ui.p("Error: Content file not found.")

def sd_tab():
    return ui.nav_panel(
        "Standard Deviation",
        ui.layout_sidebar(
            ui.sidebar(
                ui.accordion(  
                    ui.accordion_panel(
                        "What is Standard Deviation", 
                        # Place the loaded variable here
                        standard_dev_content 
                    ),
                    ui.accordion_panel("How is Standard Deviation Interpreted", "Content"),
                    
                    id="acc",  
                    open="What is Standard Deviation",
                ),
                # Keeps the sidebar from growing infinitely
                style="max-height: 80vh; overflow-y: auto;"
            ),
            ui.card(
                ui.card_header("Standard Deviation Data"),
                ui.output_plot("plot_stddev"),
                full_screen=True
            ),
        ),
    )