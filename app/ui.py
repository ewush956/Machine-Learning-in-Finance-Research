from shiny import ui
from Tabs.DataTable.datatable import datatable_tab
from Tabs.StandardDeviation.tab_stddev  import stddev_tab_ui
from stocks import stocks

import pandas  as pd

end = pd.Timestamp.now()
start = end - pd.DateOffset(years=1)

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_dark_mode(mode='dark'),
        ui.h4("Finance Metrics Dashboard"),
        ui.input_selectize("ticker", "Select Stocks", choices=stocks, selected="AAPL"),
        ui.input_date_range("dates", "Select dates", start=start, end=end),
    ),
    ui.navset_tab(
        datatable_tab(),
        stddev_tab_ui(),
    )
)