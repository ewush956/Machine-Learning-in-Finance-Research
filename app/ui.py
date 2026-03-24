from shiny import ui
from Tabs.DataTable.datatable import datatable_tab
from Tabs.StandardDeviation.tab_stddev  import stddev_tab_ui
from Tabs.SharpeRatio.tab_sharpe_ratio import sharpe_ratio_tab_ui
from pathlib import Path
import importlib.util

import pandas  as pd

end = pd.Timestamp.now()
start = end - pd.DateOffset(years=1)


def _load_ticker_choices() -> dict[str, str]:
    ticker_file = Path(__file__).resolve().parent.parent / "ticker_info.py"
    spec = importlib.util.spec_from_file_location("ticker_info_module", ticker_file)
    if spec is None or spec.loader is None:
        return {}

    ticker_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ticker_module)
    parse_query = getattr(ticker_module, "test_query", None)
    if parse_query is None:
        return {}

    ticker_map = parse_query("")
    if not isinstance(ticker_map, dict):
        return {}

    display_overrides = {
        "Apple": "Apple Inc.",
    }
    choices = {}
    for company, ticker in ticker_map.items():
        display_name = display_overrides.get(company, company)
        choices[ticker] = f"{display_name} ({ticker})"
    return dict(sorted(choices.items(), key=lambda item: item[1]))


TICKER_CHOICES = _load_ticker_choices()

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_dark_mode(mode='dark'),
        ui.h4("Finance Metrics Dashboard", align=""),
        ui.hr(),
        ui.p("Yahoo Finance Ticker Search"),
        ui.input_selectize(
            "ticker",
            "Enter Ticker",
            TICKER_CHOICES,
            selected="NVDA",
            options={
                "placeholder": "Search by company or ticker (e.g. AP, AAPL)",
                "maxOptions": 10,
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
        ui.input_date_range("dates", "Select dates", start=start, end=end),
        width="20rem"
    ),
    ui.navset_tab(
        datatable_tab(),
        stddev_tab_ui(),
        sharpe_ratio_tab_ui(),
    ),
    style="max-height: 90vh",
)