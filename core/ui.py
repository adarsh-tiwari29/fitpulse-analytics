"""Reusable UI components."""
from __future__ import annotations

import html

import numpy as np
import streamlit as st

from core.theme import LIME


def _pulse_svg(values: list[float], color: str = LIME) -> str:
    """Tiny sparkline of the 24-hour movement curve used as the signature header element."""
    v = np.asarray(values, dtype=float)
    v = (v - v.min()) / (v.max() - v.min() + 1e-9)
    w, h = 600, 90
    pts = " ".join(f"{i * w / (len(v) - 1):.1f},{h - 8 - x * (h - 20):.1f}" for i, x in enumerate(v))
    return (f'<svg class="fp-pulse" viewBox="0 0 {w} {h}" preserveAspectRatio="none">'
            f'<defs><linearGradient id="g" x1="0" x2="0" y1="0" y2="1">'
            f'<stop offset="0" stop-color="{color}" stop-opacity="0.35"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient></defs>'
            f'<polygon points="0,{h} {pts} {w},{h}" fill="url(#g)"/>'
            f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2"/></svg>')


def header(eyebrow: str, title: str, sub: str, pulse: list[float] | None = None, color: str = LIME) -> None:
    svg = _pulse_svg(pulse, color) if pulse is not None else ""
    st.markdown(f'<div class="fp-header">{svg}<div class="fp-eyebrow">{html.escape(eyebrow)}</div>'
                f'<div class="fp-title">{html.escape(title)}</div><p class="fp-sub">{sub}</p></div>',
                unsafe_allow_html=True)


def kpis(items: list[tuple]) -> None:
    """items: (label, value, hint, tone) where tone is lime/sky/coral/violet/amber or ''."""
    tiles = "".join(f'<div class="fp-kpi {t}"><div class="lbl">{l}</div><div class="val">{v}</div>'
                    f'<div class="hint">{h}</div></div>' for l, v, h, t in items)
    st.markdown(f'<div class="fp-kpis">{tiles}</div>', unsafe_allow_html=True)


def note(text: str, tone: str = "") -> None:
    st.markdown(f'<div class="fp-note {tone}">{text}</div>', unsafe_allow_html=True)


def card(title: str, body: str, big: str | None = None, color: str | None = None) -> str:
    b = f'<div class="big" style="color:{color or LIME}">{big}</div>' if big else ""
    return f'<div class="fp-card">{b}<h4>{title}</h4>{body}</div>'


def plot(fig, height: int | None = None) -> None:
    if height:
        fig.update_layout(height=height)
    st.plotly_chart(fig, config={"displayModeBar": False}, width="stretch", theme=None)
