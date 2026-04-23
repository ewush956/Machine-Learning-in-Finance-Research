from shiny import ui
from pathlib import Path
from paths import MARKDOWN_DIR

''' ========== Global Helper Functions ========== '''
def load_html(filepath: str):
    p = Path(filepath)
    print(filepath)
    if not p.is_absolute():
        p = (MARKDOWN_DIR / p).resolve()
    try:
        return ui.HTML(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return ui.p(f"Missing content file: {p}")