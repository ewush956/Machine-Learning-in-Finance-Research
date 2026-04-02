# ########################################################
# #                      Imports                         #
# ########################################################
from shiny import ui, render, reactive
from .context_builder import build_stock_context

from os import environ
import markdown
import anthropic
import math
import pandas as pd
import numpy as np


# #################################################################
# #                      Constants For LLM                        #
# #################################################################

# How many API calls one user can make in a single browser session.
# A "session" in Shiny means from the moment the app loads in their browser
# until they close or refresh it. After this limit the input disables.
# 20 is generous for personal use — tighten it if usage grows.
MAX_CALLS_PER_SESSION = 20

# The Anthropic model to use for responses.
LLM_MODEL = "claude-sonnet-4-6"

# Maximum tokens Claude is allowed to generate per response.
# 1024 tokens is roughly 700-800 words which should be enough for 
# a thorough explanation without letting responses become essays.
MAX_TOKENS = 1024

# The system prompt is sent with every API call as a standing instruction
# to Claude. It defines Claude's role, tone, and constraints for this app.
# It is NOT part of the conversation history the user sees.
#
# Key design decisions here:
SYSTEM_PROMPT = """\
You are an educational finance assistant embedded in a stock analysis dashboard.
Your job is to help people with zero finance knowledge understand what the data means.

You will always receive a STOCK CONTEXT block with real computed metrics for the
stock currently on screen. Always refer to those specific numbers in your responses.
Never speak in generalities when actual data is available.

Guidelines:
- Use plain English. Avoid jargon. If you must use a term like "volatility" or
  "Sharpe ratio", explain it in the same sentence in everyday language.
- Be encouraging and patient. The user is learning, not trading professionally.
- Auto-summaries: 3 to 5 sentences. Follow-up answers: up to 8 sentences.
- When a number suggests risk, be honest but not alarming.
- Never give specific buy or sell advice. You explain what data means, not what to do.
"""


# ###########################################################################
# #                      Metrics Computation for LLM                        #
# ###########################################################################
def _compute_metrics(
    df: pd.DataFrame,
    ticker: str,
    company_name: str,
    start_date: str,
    end_date: str,
) -> dict:
    """
    Computes all stock metrics needed by build_stock_context() from a raw
    yfinance history DataFrame.

    Returns a dictionary whose keys match exactly the parameter names of
    build_stock_context(). This means you can call:
        build_stock_context(**_compute_metrics(...))
    and it will work without any manual keyword mapping.

    Parameters
    ----------
    df : pd.DataFrame
        Raw yfinance history DataFrame. Must have a "Close" column and a
        DatetimeIndex. This is exactly what history_df() returns in server.py.

    ticker : str
        Stock symbol, e.g. "NVDA". Passed through to the output dict unchanged.

    company_name : str
        Full company name from ticker_info(). Passed through unchanged.

    start_date : str
        "YYYY-MM-DD" string for the period start. Passed through unchanged.

    end_date : str
        "YYYY-MM-DD" string for the period end. Passed through unchanged.

    Returns
    -------
    dict
        All keys needed by build_stock_context(). If df is empty or invalid,
        returns safe fallback values (zeros and NaN for Sharpe) so the rest
        of the app never crashes on missing data.
    """

    # The fallback dict is returned immediately if the data isn't usable.
    # Every numeric field defaults to 0.0 except Sharpe, which defaults to
    # float("nan") because 0.0 is a valid Sharpe ratio but NaN means
    # "could not be computed".
    fallback = dict(
        ticker=ticker,
        company_name=company_name,
        start_date=start_date,
        end_date=end_date,
        period_return_pct=0.0,
        ann_vol_pct=0.0,
        sharpe_ratio=float("nan"),
        avg_daily_move_pct=0.0,
        best_day_pct=0.0,
        worst_day_pct=0.0,
        trading_days=0,
    )
    

    if df is None or df.empty or "Close" not in df.columns:
        print("Fallback Data")
        return fallback

    close = df["Close"].dropna()

    # Need at least 2 data points to compute any meaningful return or change.
    if len(close) < 2:
        return fallback

    # pct_change() computes day-over-day % change as a decimal.
    # e.g. price goes 100 → 102, pct_change = 0.02 (meaning +2%)
    # dropna() removes the first row which is always NaN
    # (there's no "previous day" for the first data point)
    daily_returns = close.pct_change().dropna()

    # Total return from first to last close, as a percentage.
    # e.g. 100 → 142.3 gives (142.3/100 - 1) * 100 = +42.3
    period_return_pct = float((close.iloc[-1] / close.iloc[0] - 1) * 100)

    # Annualized volatility: how much the stock typically swings per year.
    # .std() gives the standard deviation of daily returns (in decimal form).
    # Multiplying by sqrt(252) scales it from a daily figure to a yearly one.
    # Multiplying by 100 converts decimal to percentage.
    # 252 is the approximate number of trading days in a calendar year.
    ann_vol_pct = float(daily_returns.std() * math.sqrt(252) * 100)

    # Average daily move: the mean of all daily % changes over the period.
    # Slightly positive even in flat markets due to how compounding works.
    avg_daily_move_pct = float(daily_returns.mean() * 100)

    # Best and worst single trading days in the period.
    # .max() and .min() find the largest and smallest values in the series.
    # Multiplying by 100 converts decimal to percentage.
    best_day_pct = float(daily_returns.max() * 100)
    worst_day_pct = float(daily_returns.min() * 100)

    # Trading days = number of rows with valid Close prices.
    # This is NOT the same as calendar days — markets are closed on
    # weekends and holidays, so a full year is ~252 days, not 365.
    trading_days = len(close)

    # The Sharpe ratio measures return relative to risk.
    # Formula: sqrt(252) * mean(excess_returns) / std(excess_returns)
    #
    # "Excess return" means return above the risk-free rate — roughly the
    # return you'd get from a government savings account risk-free.
    # We use 2% annual (0.02) as a conventional baseline.
    #
    # Converting annual 2% to a daily rate:
    # (1 + 0.02)^(1/252) - 1 ≈ 0.0000789 per day
    # This is more mathematically correct than just dividing 0.02/252.
    rf_daily = (1.0 + 0.02) ** (1.0 / 252.0) - 1.0
    excess_returns = daily_returns - rf_daily

    std_excess = float(excess_returns.std())

    # Guard against division by zero (happens if all returns are identical,
    # e.g. a stock that didn't move at all in the period).
    if std_excess > 0 and math.isfinite(std_excess):
        sharpe_ratio = float(math.sqrt(252) * excess_returns.mean() / std_excess)
    else:
        sharpe_ratio = float("nan")
        
    prompt_data = dict(
        ticker=ticker,
        company_name=company_name,
        start_date=start_date,
        end_date=end_date,
        period_return_pct=period_return_pct,
        ann_vol_pct=ann_vol_pct,
        sharpe_ratio=sharpe_ratio,
        avg_daily_move_pct=avg_daily_move_pct,
        best_day_pct=best_day_pct,
        worst_day_pct=worst_day_pct,
        trading_days=trading_days,
    )
    print(prompt_data)
    return prompt_data


async def _call_llm(system: str, messages: list[dict]) -> str:
    """
    Makes an asynchronous call to the Anthropic API and returns the
    response text.

    Parameters
    ----------
    system : str
        The system prompt. Claude's instructions for this session.
        This is the SYSTEM_PROMPT constant plus the STOCK CONTEXT block
        appended together. It is sent with every call but not stored in
        conversation history.

    messages : list[dict]
        The full conversation history in Anthropic's format:
        [
            {"role": "user",      "content": "What does high volatility mean?"},
            {"role": "assistant", "content": "High volatility means..."},
            {"role": "user",      "content": "Is that bad for me?"},
        ]
        The API is stateless, so it has no memory between calls. You must
        send the entire history every time to maintain conversation context.

    Returns
    -------
    str
        The plain text of Claude's response. If anything goes wrong,
        this raises an exception — the caller is responsible for catching it
        and showing a friendly error message to the user.

    Notes
    -----
    anthropic.AsyncAnthropic() reads the ANTHROPIC_API_KEY environment variable
    automatically. Set it in a .env file at your project root and load it with
    python-dotenv, or export it in your terminal before running the app.
    """
 
    # Creating the client inside the function rather than at module level
    # means the import only happens when an API call is actually made.
    # It also makes testing easier — you can patch this function entirely
    # without the module failing to import if the key isn't set.
    client = anthropic.AsyncAnthropic()

    response = await client.messages.create(
        model=LLM_MODEL,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=messages,
    )

    # response.content is a list of content blocks.
    # For a standard text response there will be exactly one block
    # of type "text". We access its .text attribute for the string.
    return response.content[0].text


# #######################################################
# #                      LLM UI                         #
# #######################################################
def llm_panel_ui():
    """
    Returns the UI card for the LLM assistant panel.

    This function has no logic as it just declares structure.
    It gets placed by ui.py into the collapsible right sidebar.
    All dynamic content is handled by llm_panel_server().
    """
    return ui.card(
        ui.card_header("💬 Ask the Assistant"),

        # output_ui("llm_conversation") is a dynamic slot.
        # The server fills it with styled chat bubbles whenever
        # the conversation history reactive value changes.
        ui.output_ui("llm_conversation"),
        ui.tags.script("""
            const observer = new MutationObserver(function() {
                const chat = document.getElementById("llm_conversation");
                if (chat) chat.scrollTop = chat.scrollHeight;
            });
            const target = document.getElementById("llm_conversation");
            if (target) {
                observer.observe(target, { childList: true, subtree: true });
            }
        """),

        ui.hr(),

        # This slot only renders visible content when the rate
        # limit is hit. Otherwise the server returns an empty div.
        ui.output_ui("llm_rate_warning"),

        # Input row: text field takes most of the width, Send button
        # takes the rest. col_widths must sum to 12 (Bootstrap grid).
        ui.layout_columns(
            ui.div(
                ui.input_text_area(
                    "llm_input",
                    label=None,
                    placeholder="Ask me...",
                    width="100%",
                    rows=1,
                    resize="vertical",
                ),
                ui.tags.script("""
                    const ta = document.querySelector('#llm_input textarea') || document.getElementById('llm_input');
                    if (ta) {
                        ta.addEventListener('input', function () {
                            this.style.height = 'auto';
                            this.style.height = this.scrollHeight + 'px';
                        });
                    }
                """),
            ),
            width="25rem"
        ),
        ui.input_action_button(
        "llm_send",
        "Send",
        class_="btn-primary w-100",
        style="display:block;",
        ),
    )
    
    
def llm_panel_server(
    input, output, session,
    searched_ticker,
    ticker_info,
    history_df
):
    """
    Server logic for the LLM assistant panel.

    Parameters
    ----------
    input, output, session
        Standard Shiny server arguments. Passed down from the global server
        function in server.py — same pattern as the existing tab servers.

    searched_ticker : reactive.calc
        The currently searched ticker symbol as a string. e.g. "NVDA".
        When this changes, the conversation resets and a new auto-summary fires.

    ticker_info : reactive.calc
        Dictionary of metadata from yfinance (longName, shortName, etc.).
        Used to get the company's full name for the context string.

    history_df : reactive.calc
        The raw OHLCV DataFrame for the selected ticker and date range.
        All metric calculations are derived from this.
    """

    # reactive.value() is Shiny's way of storing mutable state that triggers
    # re-renders when it changes. Think of it like a variable that the UI is
    # watching — whenever you call .set() on it, every output that depends on
    # it automatically updates.

    # The full conversation history. A list of dicts in Anthropic's format:
    # [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    # Starts empty and resets every time the user searches a new ticker.
    conversation = reactive.value([])

    # Counts how many API calls have been made this session.
    # When it reaches MAX_CALLS_PER_SESSION, the input is disabled.
    call_count = reactive.value(0)

    # These are plain functions defined inside the server function.
    # They're "inside" so they can close over the reactive values above
    # (conversation, call_count) without needing to pass them as arguments.
    # They cannot be called from outside this function.

    def _build_full_system_prompt() -> str:
        """
        Combines the static SYSTEM_PROMPT with the dynamic stock context.
        Called fresh before every API call so the context always reflects
        the current ticker and date range.
        """
        df = history_df()
        ticker = searched_ticker()
        info = ticker_info()
        company_name = info.get("longName") or info.get("shortName") or ticker

        # Pull start/end dates from the DataFrame index.
        # yfinance returns a DatetimeIndex, so .date() converts each
        # Timestamp to a plain date, and str() formats it as "YYYY-MM-DD".
        if not df.empty:
            start_date = str(df.index[0].date())
            end_date = str(df.index[-1].date())
        else:
            start_date = "N/A"
            end_date = "N/A"

        metrics = _compute_metrics(df, ticker, company_name, start_date, end_date)
        context_block = build_stock_context(**metrics)

        # The \n\n between the system prompt and context block
        # gives Claude a clear visual separator between its instructions
        # and the data it's been given to work with.
        return f"{SYSTEM_PROMPT}\n\n{context_block}"


    async def _fire_api_call(user_message: str) -> str | None:
        """
        Appends user_message to history, calls the API with the full
        conversation, appends the response, and increments the call counter.

        Returns the assistant's response string, or None if the rate limit
        has been reached or all retries are exhausted.
        """
        if not environ.get("ANTHROPIC_API_KEY") or environ.get("ANTHROPIC_API_KEY") == "placeholder":
            conversation.set(conversation() + [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": "⚠️ No API key configured. Ask your project lead for access."},
            ])
            return None
        
        if call_count() >= MAX_CALLS_PER_SESSION:
            return None

        system = _build_full_system_prompt()

        # Build the new message list: existing history + this new user message.
        # We don't mutate the existing list — we create a new one.
        # This is important because reactive.value() tracks identity,
        # and mutating the existing list in place won't trigger re-renders.
        updated_messages = conversation() + [
            {"role": "user", "content": user_message}
        ]

        # Try up to 3 times before giving up.
        # Transient network issues between Docker and Anthropic's servers
        # are the most common cause of single failures — a retry usually succeeds.
        # The call counter only increments on success so failed attempts
        # don't eat into the session limit.
        max_retries = 3

        for attempt in range(max_retries):
            try:
                response_text = str(await _call_llm(system, updated_messages))
                conversation.set(updated_messages + [
                    {"role": "assistant", "content": response_text}
                ])
                call_count.set(call_count() + 1)
                return response_text
            except Exception as e:
                print(f"[llm] attempt {attempt + 1} of {max_retries} failed: {e}")

        # All retries exhausted — show a friendly message in the chat
        # rather than silently doing nothing.
        conversation.set(updated_messages + [
            {"role": "assistant", "content": (
                f"⚠️ The assistant couldn't respond after {max_retries} attempts. "
                "Please try again in a moment."
            )},
        ])
        return None

    # ── Reactive effects ──────────────────────────────────────────────────────
    #
    # @reactive.effect marks a function that runs for its side effects
    # (updating state, firing API calls) rather than returning a value.
    #
    # @reactive.event(x) means "only re-run this effect when x changes,
    # regardless of what other reactives are accessed inside the body."
    # Without @reactive.event, Shiny would re-run the effect whenever ANY
    # reactive accessed inside it changes.
    @reactive.effect
    @reactive.event(searched_ticker)
    def _reset_on_ticker_change():
        conversation.set([])

    @reactive.effect
    @reactive.event(input.llm_send)
    async def _handle_send():
        """
        Fires when the user clicks the Send button.
        Reads the text input, clears it, and fires the API call.
        """
        user_text = (input.llm_input() or "").strip()

        # Do nothing if the input is empty or just whitespace.
        if not user_text:
            return

        # Clear the text input immediately so the user knows their
        # message was received. ui.update_text() is a Shiny helper
        # that sets an input's value from the server side.
        ui.update_text("llm_input", value="")

        await _fire_api_call(user_text)


    @render.ui
    def llm_conversation():
        """
        Renders the full conversation history as styled chat bubbles.
        Re-runs automatically whenever conversation() changes because
        it reads conversation() — that's the reactive dependency.
        """
        msgs = conversation()

        if not msgs:
            return ui.p(
                "Search a stock to get started.",
                class_="text-muted small p-2",
            )

        bubbles = []
        for msg in msgs:
            role = msg["role"]
            content = msg["content"]
            if role == "user":
                bubbles.append(
                    ui.div(
                        ui.HTML(markdown.markdown(content)),
                        class_="p-2 mb-2 rounded small",
                        style=(
                            "background-color: var(--bs-secondary-bg);"
                            "margin-left: 15%;"
                            "text-align: right;"
                        ),
                    )
                )
            else:
                bubbles.append(
                    ui.div(
                        ui.HTML(markdown.markdown(content)),
                        class_="p-2 mb-2 rounded small",
                        style=(
                            "background-color: var(--bs-tertiary-bg);"
                            "margin-right: 15%;"
                        ),
                    )
                )
            # Safety check — if content isn't a string something went wrong upstream
            if not isinstance(content, str):
                continue

        # *bubbles unpacks the list into positional arguments for ui.div().
        # ui.div(*items) is equivalent to ui.div(item1, item2, item3, ...)
        return ui.div(
            *bubbles,
            style="max-height: 420px; overflow-y: auto; padding: 0.5rem;",
        )

    @render.ui
    def llm_rate_warning():
        """
        Shows a warning when the session call limit is reached.
        Returns an empty div when under the limit so it takes no space.
        """
        if call_count() >= MAX_CALLS_PER_SESSION:
            return ui.div(
                ui.p(
                    f"⚠️ You've used all {MAX_CALLS_PER_SESSION} questions for this session. "
                    "Refresh the page to start fresh.",
                    class_="text-warning small mb-0",
                ),
                class_="p-2",
            )
        return ui.div()