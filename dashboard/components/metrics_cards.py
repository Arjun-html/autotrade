"""Reusable metric display widgets for the Streamlit dashboard."""

from __future__ import annotations

import streamlit as st


def metric_row(metrics: dict[str, tuple[str, str | None]]) -> None:
    """Render a horizontal row of st.metric cards.

    Args:
        metrics: Mapping of label → (value_string, optional_delta_string).
                 Example: {"Sharpe": ("1.42", "+0.05"), "VaR 95%": ("-2.1%", None)}
    """
    cols = st.columns(len(metrics))
    for col, (label, (value, delta)) in zip(cols, metrics.items()):
        col.metric(label=label, value=value, delta=delta)


def status_badge(label: str, active: bool) -> str:
    """Return an HTML badge string for use with st.markdown(..., unsafe_allow_html=True).

    Args:
        label: Badge text.
        active: Green if True, red if False.

    Returns:
        HTML string.
    """
    colour = "#26a69a" if active else "#ef5350"
    return (
        f'<span style="background:{colour};color:white;padding:2px 8px;'
        f'border-radius:4px;font-size:0.8rem;">{label}</span>'
    )
