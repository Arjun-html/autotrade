"""Signals page — current trade ideas, predicted returns, and signal history.

This page will show live signal output once the Signal Generator module is
implemented. For now it renders a clearly structured placeholder that
matches the intended final layout.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

st.set_page_config(
    page_title="Signals — AutoTrade",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ Signal Generator")

with st.sidebar:
    st.header("⚡ Signals")
    st.divider()
    st.info(
        "Configure signal generators and run parameters once the module is implemented."
    )

# ── Status banner ─────────────────────────────────────────────────────────────

st.info(
    "The Signal Generator module is **not yet implemented**. "
    "This page shows the planned layout. Come back after the module is built.",
    icon="🔧",
)

st.divider()

# ── Planned layout preview ────────────────────────────────────────────────────

st.subheader("Active Signals")
st.markdown(
    """
    *Once implemented, this table will display signals produced by all active generators:*

    | Symbol | Direction | Confidence | Predicted Return | Horizon | Generator | Generated At |
    |--------|-----------|-----------|-----------------|---------|-----------|-------------|
    | AAPL   | 🟢 Long   | 78%        | +2.4%           | 5 days  | LSTM      | —           |
    | MSFT   | 🟢 Long   | 65%        | +1.1%           | 1 day   | ARIMA     | —           |
    | NVDA   | 🔴 Short  | 55%        | -1.8%           | 3 days  | Sentiment | —           |
    """
)

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📈 Time Series Models")
    st.markdown(
        """
        **Planned generators:**
        - ARIMA / SARIMA
        - Holt-Winters exponential smoothing
        - Prophet (Facebook)

        These models analyse historical price patterns to forecast short-term
        directional moves.
        """
    )

with col2:
    st.subheader("🧠 Neural Networks")
    st.markdown(
        """
        **Planned generators:**
        - LSTM (Long Short-Term Memory)
        - Temporal Fusion Transformer
        - Encoder-Decoder sequence model

        Deep learning models trained on OHLCV + technical features
        to capture non-linear patterns.
        """
    )

with col3:
    st.subheader("💬 LLM Sentiment")
    st.markdown(
        """
        **Planned generators:**
        - News headline sentiment (OpenAI / Anthropic)
        - Earnings call transcript analysis
        - Reddit / social media sentiment

        Language model signals that quantify market sentiment from
        unstructured text sources.
        """
    )

st.divider()

st.subheader("Ensemble Signal")
st.markdown(
    """
    *The Ensemble Signal Generator will combine outputs from all active generators
    using configurable weighting (e.g. equal weight, confidence-weighted, or
    trained meta-model) to produce a single consolidated signal per symbol.*
    """
)
