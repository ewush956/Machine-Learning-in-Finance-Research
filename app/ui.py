from shiny import ui
from Tabs.DataTable.datatable import datatable_tab
from Tabs.StandardDeviation.tab_stddev  import stddev_tab_ui

import pandas  as pd

end = pd.Timestamp.now()
start = end - pd.DateOffset(years=1)

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_dark_mode(mode='dark'),
        ui.h4("Finance Metrics Dashboard", align=""),
        ui.hr(),
        ui.p("Yahoo Finance Ticker Search"),
        ui.input_text("ticker", "Enter Ticker", placeholder="e.g. AAPL"),
        ui.input_action_button("search", "Search"),
        ui.input_date_range("dates", "Select dates", start=start, end=end),
    ),
    ui.navset_tab(
        datatable_tab(),
        stddev_tab_ui(),
    )
)