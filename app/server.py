from pathlib import Path
from shiny import Inputs, Outputs, Session, render
import pandas

UPLOAD_DIR = Path("data/uploads")
TEST_DATA = Path("data/test/TEST_DATA_NVIDIA.xlsx")


def server(input: Inputs, output: Outputs, session: Session):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    @render.text
    def _noop() -> str:
        return ""

    @render.data_frame
    def imported_data():
        df = pandas.read_excel(TEST_DATA)
        return render.DataGrid(df, filters=True)
