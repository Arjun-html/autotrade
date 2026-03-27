"""Portfolio page — current holdings, allocation, P&L, and risk metrics.

This page will be fully wired once the Portfolio Manager is implemented.
For now it connects to the Alpaca paper account directly to show live
positions and account info.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from config import settings
from dashboard.components.charts import allocation_pie
from dashboard.components.metrics_cards import metric_row

st.set_page_config(
    page_title="Portfolio — AutoTrade",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Portfolio")

with st.sidebar:
    st.header("📊 Portfolio")
    st.divider()
    st.info("Portfolio optimisation and risk metrics will be available once the Portfolio Manager module is implemented.")

if not settings.alpaca_api_key:
    st.warning("Alpaca API key not set. Add your credentials to `.env` and restart.", icon="⚠️")
    st.stop()

# ── Account summary via Alpaca trading client ─────────────────────────────────

@st.cache_resource(show_spinner="Connecting to Alpaca trading API…")
def get_trading_client():
    from alpaca.trading.client import TradingClient

    return TradingClient(
        api_key=settings.alpaca_api_key,
        secret_key=settings.alpaca_secret_key,
        paper=settings.paper_trading,
    )


with st.spinner("Loading account data…"):
    try:
        client = get_trading_client()
        account = client.get_account()
        positions = client.get_all_positions()
        has_data = True
    except Exception as exc:
        st.error(f"Failed to connect to Alpaca: {exc}")
        has_data = False

if not has_data:
    st.stop()

# ── Account metrics row ───────────────────────────────────────────────────────

equity = float(account.equity)
cash = float(account.cash)
buying_power = float(account.buying_power)
day_pl = float(account.equity) - float(account.last_equity)
day_pl_pct = (day_pl / float(account.last_equity) * 100) if float(account.last_equity) else 0

metric_row(
    {
        "Portfolio Equity": (f"${equity:,.2f}", f"{day_pl_pct:+.2f}% today"),
        "Cash": (f"${cash:,.2f}", None),
        "Buying Power": (f"${buying_power:,.2f}", None),
        "Day P&L": (
            f"${day_pl:+,.2f}",
            f"{day_pl_pct:+.2f}%",
        ),
        "Positions": (str(len(positions)), None),
    }
)

st.divider()

# ── Positions table ───────────────────────────────────────────────────────────

st.subheader("Open Positions")

if not positions:
    st.info("No open positions. The paper account is currently flat.")
else:
    import pandas as pd

    rows = []
    weights: dict[str, float] = {}

    for pos in positions:
        market_val = float(pos.market_value)
        cost_basis = float(pos.cost_basis)
        unrealised_pl = float(pos.unrealized_pl)
        unrealised_plpc = float(pos.unrealized_plpc) * 100
        rows.append(
            {
                "Symbol": pos.symbol,
                "Qty": float(pos.qty),
                "Avg Entry": f"${float(pos.avg_entry_price):,.2f}",
                "Current Price": f"${float(pos.current_price):,.2f}",
                "Market Value": f"${market_val:,.2f}",
                "Unrealised P&L": f"${unrealised_pl:+,.2f}",
                "P&L %": f"{unrealised_plpc:+.2f}%",
                "Side": pos.side.value if hasattr(pos.side, "value") else str(pos.side),
            }
        )
        weights[pos.symbol] = abs(market_val)

    df = pd.DataFrame(rows).set_index("Symbol")
    st.dataframe(df, use_container_width=True)

    # Normalise weights for the pie chart
    total_mv = sum(weights.values())
    if total_mv > 0:
        norm_weights = {k: v / total_mv for k, v in weights.items()}
        col1, col2 = st.columns([1, 1])
        with col1:
            fig = allocation_pie(norm_weights, "Current Allocation by Market Value")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.subheader("Risk Metrics")
            st.info(
                "Detailed risk metrics (Sharpe ratio, VaR, CVaR, max drawdown, beta) "
                "will be available once the Portfolio / Risk Manager module is implemented.",
                icon="🔧",
            )

st.divider()

# ── Portfolio optimiser placeholder ──────────────────────────────────────────

st.subheader("Portfolio Optimiser")
st.info(
    """
    **Coming soon:** This panel will allow you to run portfolio optimisation
    using the following methods:

    - **Mean-Variance (MPT)** — maximise Sharpe ratio subject to weight constraints
    - **Black-Litterman** — blend market equilibrium with analyst views
    - **Risk Parity** — equal risk contribution from each asset
    - **Factor Models** — Fama-French factor exposure targeting
    """,
    icon="🔧",
)
