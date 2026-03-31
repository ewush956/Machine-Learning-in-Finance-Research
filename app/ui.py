# #########################################################
# #                      Imports                          #
# #########################################################
from shiny import ui
from Tabs.DataTable.datatable import datatable_tab_ui
from Tabs.StandardDeviation.tab_stddev  import stddev_tab_ui
from Tabs.SharpeRatio.tab_sharpe_ratio import sharpe_ratio_tab_ui
from llm_panel import llm_panel_ui
from ticker_info import company_tickers

import pandas  as pd


# ###########################################################
# #                      Constants                          #
# ###########################################################
END_DATE = pd.Timestamp.now()
START_DATE = END_DATE - pd.DateOffset(years=1)


# ################################################################
# #                      File Functions                          #
# ################################################################
def _load_ticker_choices() -> dict[str, str]:
    choices = {}
    for company, ticker in company_tickers.items():
        choices[ticker] = f"{company} ({ticker})"
    return dict(sorted(choices.items(), key=lambda item: item[1]))


# #####################################################################
# #                      Application UI Main                          #
# #####################################################################
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_dark_mode(id="color_mode", mode='dark'),
        ui.h4("Finance Metrics Dashboard", align=""),
        ui.p("Yahoo Finance Ticker Search"),
        ui.input_selectize(
            "ticker",
            "Enter Ticker",
            choices = _load_ticker_choices(),
            selected="",
            options={
                "placeholder": "Search by company or ticker",
                "maxOptions": 25,
            },
        ),
        ui.input_action_button("search", "Search"),
        ui.tags.script(
            """
            document.addEventListener("shiny:connected", function () {
                const tickerInput = document.getElementById("ticker");
                const searchButton = document.getElementById("search");
                if (!tickerInput || !searchButton) return;
                const defaultTicker = "NVDA";

                const ensureDefaultTicker = function () {
                    const selectize = tickerInput.selectize;
                    if (selectize) {
                        let valueToSet = null;
                        if (Object.prototype.hasOwnProperty.call(selectize.options, defaultTicker)) {
                            valueToSet = defaultTicker;
                        } else {
                            for (const [value, option] of Object.entries(selectize.options)) {
                                const text = String(option.text || "").toUpperCase();
                                if (text.includes("(" + defaultTicker + ")")) {
                                    valueToSet = value;
                                    break;
                                }
                            }
                        }
                        if (valueToSet && selectize.getValue() !== valueToSet) {
                            selectize.setValue(valueToSet, true);
                        }
                        return;
                    }

                    if (!tickerInput.value) {
                        tickerInput.value = defaultTicker;
                    }
                };

                const triggerInitialSearch = function () {
                    ensureDefaultTicker();
                    if (!window.__initialTickerSearchDone && tickerInput.value) {
                        window.__initialTickerSearchDone = true;
                        searchButton.click();
                    }
                };

                setTimeout(triggerInitialSearch, 0);
                setTimeout(triggerInitialSearch, 200);

                tickerInput.addEventListener("change", function () {
                    if (tickerInput.value) {
                        searchButton.click();
                    }
                });
            });
            """
        ),
        ui.input_date_range("dates", "Select dates", start=START_DATE, end=END_DATE),
        llm_panel_ui(),
        width="20rem"
    ),
    ui.layout_columns(
        ui.navset_tab(
            datatable_tab_ui(),
            stddev_tab_ui(),
            sharpe_ratio_tab_ui(),
        ),
    ),
    style="max-height: 90vh",
)