"""Market Data page — historical charts, latest quotes, and asset explorer.

This is the first fully wired page: it uses the real AlpacaDataProvider
(wrapped in DataCache) to fetch and display actual market data.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from config import settings
from data.cache import DataCache
from data.models import Timeframe
from data.providers.alpaca import AlpacaDataProvider
from dashboard.components.charts import candlestick_chart
from dashboard.components.metrics_cards import metric_row

st.set_page_config(
    page_title="Market Data — AutoTrade",
    page_icon="🗄️",
    layout="wide",
)

# ─────────────────────────────── provider setup (cached at session level) ────

@st.cache_resource(show_spinner="Connecting to Alpaca data API…")
def get_data_provider() -> DataCache:
    """Initialise the data provider once per Streamlit session."""
    raw_provider = AlpacaDataProvider(
        api_key=settings.alpaca_api_key,
        secret_key=settings.alpaca_secret_key,
        feed=settings.alpaca_data_feed,
        paper=settings.paper_trading,
    )
    return DataCache(
        provider=raw_provider,
        cache_dir=settings.cache_dir,
        ttl_seconds=settings.cache_ttl_seconds,
    )


# ───────────────────────────────────────────────── sidebar controls ──────────

with st.sidebar:
    st.header("🗄️ Market Data")
    st.divider()

    symbol = st.text_input(
        "Symbol",
        value="AAPL",
        help="Enter a US equity ticker (e.g. AAPL, MSFT, NVDA)",
    ).upper().strip()

    timeframe_labels = {
        "1 Day": Timeframe.DAY_1,
        "1 Hour": Timeframe.HOUR_1,
        "30 Min": Timeframe.MIN_30,
        "15 Min": Timeframe.MIN_15,
        "5 Min": Timeframe.MIN_5,
        "1 Min": Timeframe.MIN_1,
    }
    tf_label = st.selectbox("Timeframe", list(timeframe_labels.keys()), index=0)
    timeframe = timeframe_labels[tf_label]

    lookback_options = {
        "1 Week": 7,
        "1 Month": 30,
        "3 Months": 90,
        "6 Months": 180,
        "1 Year": 365,
        "2 Years": 730,
    }
    lookback_label = st.selectbox("Lookback", list(lookback_options.keys()), index=3)
    lookback_days = lookback_options[lookback_label]

    show_volume = st.toggle("Show volume", value=True)

    st.divider()
    watchlist_input = st.text_area(
        "Watchlist (one per line)",
        value="\n".join(settings.default_symbols),
        height=130,
    )
    watchlist = [s.strip().upper() for s in watchlist_input.splitlines() if s.strip()]

    refresh = st.button("🔄 Refresh", use_container_width=True)

# ──────────────────────────────────────────────── main panel ─────────────────

st.title("🗄️ Market Data")

if not settings.alpaca_api_key:
    st.warning(
        "**Alpaca API key not set.** Copy `.env.example` to `.env` and add your paper "
        "trading credentials, then restart the app.",
        icon="⚠️",
    )
    st.stop()

provider = get_data_provider()

# ── Latest quote bar ─────────────────────────────────────────────────────────

with st.spinner(f"Fetching latest data for {symbol}…"):
    latest = provider.get_latest_bar(symbol)
    quote = provider.get_latest_quote(symbol)
    asset = provider.get_asset(symbol)

if latest is None:
    st.error(f"No data found for **{symbol}**. Check the ticker or try again.")
    st.stop()

# Header metrics
price_delta = f"{latest.return_ * 100:+.2f}%" if latest else None
metrics = {
    "Last Close": (f"${latest.close:,.2f}", price_delta),
    "Open": (f"${latest.open:,.2f}", None),
    "High": (f"${latest.high:,.2f}", None),
    "Low": (f"${latest.low:,.2f}", None),
    "Volume": (f"{int(latest.volume):,}", None),
}
if quote:
    metrics["Bid / Ask"] = (f"${quote.bid_price:.2f} / ${quote.ask_price:.2f}", None)
    metrics["Spread"] = (f"${quote.spread:.4f}", None)

metric_row(metrics)

if asset:
    st.caption(
        f"**{asset.name}** · {asset.exchange} · "
        f"{'Tradable ✅' if asset.tradable else 'Not tradable ❌'} · "
        f"{'Fractionable' if asset.fractionable else ''} · "
        f"{'Shortable' if asset.shortable else ''}"
    )

st.divider()

# ── Candlestick chart ─────────────────────────────────────────────────────────

end_dt = datetime.now(timezone.utc)
start_dt = end_dt - timedelta(days=lookback_days)

with st.spinner(f"Loading {lookback_days}d of {tf_label} bars…"):
    df = provider.get_bars(symbol, start_dt, end_dt, timeframe)

if df.empty:
    st.warning(f"No historical bars returned for **{symbol}** with the selected parameters.")
else:
    fig = candlestick_chart(df, symbol, volume=show_volume)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        f"{len(df):,} bars · {df.index[0].strftime('%Y-%m-%d')} → "
        f"{df.index[-1].strftime('%Y-%m-%d')} · Feed: {settings.alpaca_data_feed.upper()}"
    )

st.divider()

# ── Watchlist snapshot ────────────────────────────────────────────────────────

st.subheader("Watchlist Snapshot")

with st.spinner("Fetching latest bars for watchlist…"):
    latest_bars = provider.get_latest_bars(watchlist)

watchlist_rows = []
for sym, bar in latest_bars.items():
    if bar:
        watchlist_rows.append(
            {
                "Symbol": sym,
                "Close": f"${bar.close:,.2f}",
                "Open": f"${bar.open:,.2f}",
                "High": f"${bar.high:,.2f}",
                "Low": f"${bar.low:,.2f}",
                "Change": f"{bar.return_ * 100:+.2f}%",
                "Volume": f"{int(bar.volume):,}",
            }
        )
    else:
        watchlist_rows.append({"Symbol": sym, "Close": "—", "Open": "—", "High": "—", "Low": "—", "Change": "—", "Volume": "—"})

if watchlist_rows:
    import pandas as pd

    wl_df = pd.DataFrame(watchlist_rows).set_index("Symbol")
    st.dataframe(wl_df, use_container_width=True)

st.divider()

# ── Raw data table ────────────────────────────────────────────────────────────

with st.expander("📋 Raw bar data", expanded=False):
    if not df.empty:
        st.dataframe(df.tail(100).iloc[::-1], use_container_width=True)
    else:
        st.info("No data to display.")
