from shiny import ui

''' ========== Global Helper Functions ========== '''
def load_html(filepath: str):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return ui.HTML(f.read())
    except FileNotFoundError:
        return ui.p(f"Missing content file: {filepath}")