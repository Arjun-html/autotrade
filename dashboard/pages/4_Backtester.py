"""Backtester page — run strategy simulations and view performance reports.

This page will be fully wired once the BacktestEngine is implemented.
For now it renders the planned layout with a clearly labelled placeholder.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

st.set_page_config(
    page_title="Backtester — AutoTrade",
    page_icon="🔬",
    layout="wide",
)

st.title("🔬 Backtester")

with st.sidebar:
    st.header("🔬 Backtester")
    st.divider()

    st.subheader("Run Configuration")
    symbols_input = st.text_input("Symbols (comma-separated)", value="AAPL,MSFT,NVDA")
    start_date = st.date_input("Start date")
    end_date = st.date_input("End date")
    initial_capital = st.number_input(
        "Initial capital (USD)", value=100_000, step=10_000, min_value=1_000
    )
    commission = st.slider("Commission (%)", min_value=0.0, max_value=0.5, value=0.1, step=0.01)
    slippage = st.slider("Slippage (bps)", min_value=0, max_value=20, value=5)

    run_btn = st.button("▶ Run Backtest", use_container_width=True, disabled=True)
    if run_btn:
        st.warning("BacktestEngine not yet implemented.")

# ── Status banner ─────────────────────────────────────────────────────────────

st.info(
    "The Backtester module is **not yet implemented**. "
    "This page shows the planned layout. The sidebar controls are wired — "
    "they will trigger a real backtest once the engine is built.",
    icon="🔧",
)

st.divider()

# ── Planned layout ────────────────────────────────────────────────────────────

st.subheader("Equity Curve")
st.markdown(
    "*Once implemented, an interactive equity curve will appear here comparing "
    "the strategy against a buy-and-hold benchmark.*"
)

st.divider()

col1, col2, col3, col4, col5 = st.columns(5)
placeholders = {
    "Total Return": "—",
    "CAGR": "—",
    "Sharpe Ratio": "—",
    "Max Drawdown": "—",
    "Win Rate": "—",
}
for col, (label, val) in zip([col1, col2, col3, col4, col5], placeholders.items()):
    col.metric(label=label, value=val)

st.divider()

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Trade Log")
    st.markdown(
        """
        *All simulated trades will be listed here, including:*

        | Entry Time | Exit Time | Symbol | Side | Qty | Entry Price | Exit Price | P&L |
        |-----------|----------|--------|------|-----|-------------|------------|-----|
        | — | — | — | — | — | — | — | — |
        """
    )

with col_b:
    st.subheader("Monthly Returns Heatmap")
    st.markdown(
        "*A calendar heatmap of monthly returns will be displayed here.*"
    )

st.divider()

st.subheader("Backtest Engine Design")
st.markdown(
    """
    The backtester will use an **event-driven** architecture:

    1. Load historical OHLCV bars from `DataProvider` for all symbols
    2. Iterate through bars in chronological order
    3. At each bar, call `SignalGenerator.generate()` to produce signals
    4. Pass signals through a simplified `PortfolioManager` for sizing
    5. Simulate fills at the **next bar's open** with slippage + commission
    6. Track equity curve, positions, and trade log
    7. Compute performance metrics via `backtester.metrics`

    **Supported metrics:** CAGR, Sharpe, Sortino, Max Drawdown, Calmar,
    Win Rate, Profit Factor, Average Trade, Monthly Returns.
    """
)
