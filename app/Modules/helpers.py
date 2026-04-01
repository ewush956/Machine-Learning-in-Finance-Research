from shiny import ui
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent

''' ========== Global Helper Functions ========== '''
def load_html(filepath: str):
    p = Path(filepath)
    if not p.is_absolute():
        p = (APP_DIR / p).resolve()
    try:
        return ui.HTML(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return ui.p(f"Missing content file: {p}")