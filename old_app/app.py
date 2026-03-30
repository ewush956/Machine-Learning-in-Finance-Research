from shiny import App # Shiny Core application object
from ui import app_ui # Our defined UI for layout etc.
from server import server # Our Server logic where plots, tables, and calculations etc. live.
from plot_theme import apply_matplotlib_theme

apply_matplotlib_theme("dark")
app = App(
    app_ui, server
)  # This creates the runnable Shiny app by pairing the UI and Server together
