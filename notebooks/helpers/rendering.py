"""Reusable display helpers for WalletMind Kaggle notebooks (K1-K4)."""

from __future__ import annotations

from html import escape
from typing import Iterable, Sequence

try:
    from IPython.display import HTML, Markdown, display
except ModuleNotFoundError:  # pragma: no cover - fallback for non-notebook shells
    class _TextDisplay(str):
        pass

    def HTML(value: str) -> _TextDisplay:  # type: ignore[misc]
        return _TextDisplay(value)

    def Markdown(value: str) -> _TextDisplay:  # type: ignore[misc]
        return _TextDisplay(value)

    def display(value) -> None:  # type: ignore[misc]
        print(value)


def _join(items: Iterable[str], sep: str = "") -> str:
    return sep.join(items)


def render_badge(label: str, tone: str = "neutral") -> str:
    """Return an inline HTML badge string."""

    tone_map = {
        "neutral": ("#e5e7eb", "#111827"),
        "primary": ("#dbeafe", "#1e3a8a"),
        "success": ("#dcfce7", "#14532d"),
        "accent": ("#fef3c7", "#78350f"),
    }
    bg, fg = tone_map.get(tone, tone_map["neutral"])
    safe = escape(label)
    return (
        f"<span style=\"display:inline-block;padding:6px 10px;margin:4px;"
        f"border-radius:999px;background:{bg};color:{fg};font-size:12px;"
        f"font-weight:600;border:1px solid rgba(17,24,39,0.08);\">{safe}</span>"
    )


def render_title(title: str, subtitle: str = "", description: str = "") -> None:
    """Render a notebook hero title block."""

    html = [
        "<div style='padding:28px;border-radius:18px;",
        "background:linear-gradient(135deg,#0f172a 0%,#1e293b 45%,#334155 100%);",
        "color:#f8fafc;margin:12px 0 16px 0;'>",
        f"<h1 style='margin:0;font-size:44px;line-height:1.1;'>{escape(title)}</h1>",
    ]
    if subtitle:
        html.append(
            f"<p style='margin:10px 0 0 0;font-size:20px;font-weight:600;opacity:0.95;'>{escape(subtitle)}</p>"
        )
    if description:
        html.append(
            f"<p style='margin:12px 0 0 0;font-size:15px;opacity:0.9;max-width:960px;'>{escape(description)}</p>"
        )
    html.append("</div>")
    display(HTML(_join(html)))


def render_section(title: str, anchor: str = "") -> None:
    """Render a large section heading."""

    safe_title = escape(title)
    if anchor:
        display(Markdown(f"## <a id='{escape(anchor)}'></a>{safe_title}"))
        return
    display(Markdown(f"## {safe_title}"))


def render_callout(title: str, body: str, tone: str = "info") -> None:
    """Render a styled callout panel."""

    palette = {
        "info": ("#eff6ff", "#1e40af", "#1e3a8a"),
        "success": ("#ecfdf5", "#047857", "#064e3b"),
        "warning": ("#fff7ed", "#c2410c", "#7c2d12"),
    }
    bg, border, fg = palette.get(tone, palette["info"])
    display(
        HTML(
            """
            <div style="padding:14px 16px;margin:10px 0 16px 0;border-radius:12px;">
            """.strip()
            + f"background:{bg};border-left:6px solid {border};color:{fg};"
            + f"<div style='font-weight:700;margin-bottom:4px;'>{escape(title)}</div>"
            + f"<div style='font-size:14px;line-height:1.5;'>{body}</div>"
            + "</div>"
        )
    )


def render_card(title: str, body: str, footer: str = "") -> str:
    """Return an HTML card block for grid layouts."""

    parts = [
        "<div style='padding:14px;border:1px solid #e2e8f0;border-radius:12px;",
        "background:#ffffff;box-shadow:0 2px 12px rgba(15,23,42,0.05);height:100%;'>",
        f"<h4 style='margin:0 0 8px 0;font-size:16px;color:#0f172a;'>{escape(title)}</h4>",
        f"<p style='margin:0;font-size:14px;color:#334155;line-height:1.45;'>{body}</p>",
    ]
    if footer:
        parts.append(
            f"<p style='margin:10px 0 0 0;font-size:12px;color:#64748b;'>{escape(footer)}</p>"
        )
    parts.append("</div>")
    return _join(parts)


def render_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> None:
    """Render a simple HTML table for architecture/stack summaries."""

    thead = _join(
        [f"<th style='text-align:left;padding:10px;background:#f8fafc;border-bottom:1px solid #e2e8f0;'>{escape(h)}</th>" for h in headers]
    )
    body_rows = []
    for row in rows:
        cols = _join(
            [f"<td style='padding:10px;border-bottom:1px solid #f1f5f9;vertical-align:top;'>{escape(col)}</td>" for col in row]
        )
        body_rows.append(f"<tr>{cols}</tr>")

    html = (
        "<div style='overflow-x:auto;'><table style='width:100%;border-collapse:collapse;font-size:14px;'>"
        + f"<thead><tr>{thead}</tr></thead><tbody>{_join(body_rows)}</tbody></table></div>"
    )
    display(HTML(html))
