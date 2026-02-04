from shiny import App
from app.ui import app_ui
from app.server import server

app = App(app_ui, server)
