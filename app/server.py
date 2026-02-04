from pathlib import Path
from shiny import Inputs, Outputs, Session, render

UPLOAD_DIR = Path("data/uploads")


def server(input: Inputs, output: Outputs, session: Session):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    @render.text
    def _noop() -> str:
        return ""
