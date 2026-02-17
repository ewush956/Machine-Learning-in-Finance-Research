from shiny import ui
from Tabs.DataTable.datatable import datatable_tab
from Tabs.StandardDeviation.tab_stddev  import stddev_tab_ui

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_dark_mode(mode='dark'),
        ui.h4("Finance Metrics Dashboard"),
    ),
    ui.navset_tab(
        datatable_tab(),
        stddev_tab_ui(),
    )
)