"""AutoTrade — Streamlit dashboard entry point.

Run with:
    streamlit run dashboard/app.py

The multipage navigation is handled automatically by Streamlit via the
pages/ sub-directory. This file configures global page settings and renders
the home / overview page.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is on sys.path so all modules resolve correctly
# when Streamlit is launched from inside the dashboard/ folder.
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from config import settings

st.set_page_config(
    page_title=settings.dashboard_title,
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────── custom CSS ──────────────────────

st.markdown(
    """
    <style>
    /* Dark card style for metric containers */
    [data-testid="metric-container"] {
        background: #1e2130;
        border: 1px solid #2d3250;
        border-radius: 8px;
        padding: 12px 16px;
    }
    /* Sidebar accent */
    section[data-testid="stSidebar"] {
        background: #161928;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ───────────────────────────────────────────── sidebar ───────────────────────

with st.sidebar:
    st.title("📈 AutoTrade")
    st.caption("Algorithmic Trading System")
    st.divider()

    paper_badge = "🟢 Paper Trading" if settings.paper_trading else "🔴 Live Trading"
    st.markdown(paper_badge)

    feed_label = settings.alpaca_data_feed.upper()
    st.markdown(f"Data feed: **{feed_label}**")

    st.divider()
    st.caption("Navigate using the pages in the sidebar above.")

# ─────────────────────────────────────────── home page ───────────────────────

st.title("📈 AutoTrade — Overview")
st.markdown(
    """
    Welcome to **AutoTrade**, a modular algorithmic trading system built on Alpaca's
    paper trading API. Use the sidebar to navigate between modules.
    """
)

st.divider()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("### 🗄️ Market Data")
    st.markdown(
        """
        Historical and live OHLCV data from Alpaca.  
        Feeds all other system components.  
        **Status:** ✅ Implemented
        """
    )

with col2:
    st.markdown("### ⚡ Signals")
    st.markdown(
        """
        Trade ideas from time-series models,  
        neural networks, and LLM sentiment.  
        **Status:** 🔧 Coming soon
        """
    )

with col3:
    st.markdown("### 📊 Portfolio")
    st.markdown(
        """
        MPT / Black-Litterman optimisation,  
        risk metrics, and trade approval.  
        **Status:** 🔧 Coming soon
        """
    )

with col4:
    st.markdown("### 🔬 Backtester")
    st.markdown(
        """
        Event-driven strategy backtesting  
        on historical Alpaca data.  
        **Status:** 🔧 Coming soon
        """
    )

st.divider()

st.markdown("### System Architecture")
st.markdown(
    """
    ```
    Market Data Collector  ──→  Signal Generator  ──→  Portfolio / Risk Manager
           │                                                       │
           └──────────────────────────────────────────→  Backtester
                                                                   │
                                                         Execution (Alpaca Paper)
    ```
    """
)
