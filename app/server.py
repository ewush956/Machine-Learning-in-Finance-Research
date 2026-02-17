from pathlib import Path
from shiny import Inputs, Outputs, Session, ui
from Tabs.DataTable.datatable import datatable_tab_server
from Tabs.StandardDeviation.tab_stddev import stddev_tab_server

TEST_EXCEL_PATH = Path(__file__).resolve().parent / "Data" / "Test" / "TEST_DATA_NVIDIA.xlsx"

''' ========== Global Server ========== '''
def server(input: Inputs, output: Outputs, session: Session):
    datatable_tab_server(input, output, session, data_path=TEST_EXCEL_PATH)
    stddev_tab_server(input, output, session, data_path=TEST_EXCEL_PATH)
