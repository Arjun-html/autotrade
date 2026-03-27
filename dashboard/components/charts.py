"""Reusable Plotly chart helpers for the Streamlit dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def candlestick_chart(
    df: pd.DataFrame,
    symbol: str,
    volume: bool = True,
) -> go.Figure:
    """Render an OHLCV candlestick chart with optional volume subplot.

    Args:
        df: DataFrame with columns [open, high, low, close, volume] and a DatetimeIndex.
        symbol: Ticker label shown in the chart title.
        volume: Whether to include a volume bar subplot below the candles.

    Returns:
        Plotly Figure ready for st.plotly_chart().
    """
    rows = 2 if volume else 1
    row_heights = [0.7, 0.3] if volume else [1.0]

    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
    )

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name=symbol,
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
        ),
        row=1,
        col=1,
    )

    if volume:
        colours = [
            "#26a69a" if c >= o else "#ef5350"
            for c, o in zip(df["close"], df["open"])
        ]
        fig.add_trace(
            go.Bar(x=df.index, y=df["volume"], name="Volume", marker_color=colours),
            row=2,
            col=1,
        )

    fig.update_layout(
        title=f"{symbol} Price",
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        height=500,
        margin=dict(l=40, r=20, t=50, b=20),
    )
    return fig


def equity_curve_chart(equity: pd.Series, title: str = "Portfolio Equity") -> go.Figure:
    """Line chart of a portfolio equity curve.

    Args:
        equity: Series of portfolio value indexed by datetime.
        title: Chart title.

    Returns:
        Plotly Figure.
    """
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=equity.index,
            y=equity.values,
            mode="lines",
            name="Equity",
            line=dict(color="#29b6f6", width=2),
            fill="tozeroy",
            fillcolor="rgba(41, 182, 246, 0.1)",
        )
    )
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Value (USD)",
        template="plotly_dark",
        height=400,
        margin=dict(l=40, r=20, t=50, b=20),
    )
    return fig


def allocation_pie(weights: dict[str, float], title: str = "Portfolio Allocation") -> go.Figure:
    """Donut chart of portfolio weights.

    Args:
        weights: Mapping of symbol → weight fraction.
        title: Chart title.

    Returns:
        Plotly Figure.
    """
    fig = go.Figure(
        go.Pie(
            labels=list(weights.keys()),
            values=list(weights.values()),
            hole=0.45,
            textinfo="label+percent",
        )
    )
    fig.update_layout(
        title=title,
        template="plotly_dark",
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig
