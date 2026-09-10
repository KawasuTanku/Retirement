"""ASCII chart module — diverging horizontal bar chart centered at zero."""

from __future__ import annotations

from typing import Any


# ANSI color codes
RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


def render_bar_chart(data: dict[str, Any], width: int = 70, bars_only: bool = False) -> str:
    """Render a diverging horizontal bar chart with center at zero.

    Losses extend left (red), gains extend right (green).
    Dollar amount + percentage shown at bar end.
    """
    holdings = data.get("holdings", []) or data.get("combined", [])
    if not holdings:
        return "No holdings data available."

    lines = []

    # Header
    total_value = data.get("total_value", 0)
    total_cost = data.get("total_cost_basis", 0)
    total_gl = data.get("total_gain_loss", 0)
    total_gl_pct = (total_gl / total_cost * 100) if total_cost > 0 else 0

    # Use half-width for each direction (left/right of center)
    half_width = width // 2

    if not bars_only:
        lines.append("=" * (width + 55))
        lines.append(f"  {BOLD}RETIREMENT PORTFOLIO — Gain/Loss by Holding{RESET}")
        lines.append(f"  Last updated: {data.get('last_updated', 'Unknown')}")
        lines.append("=" * (width + 55))
        lines.append("")

    # Find max absolute value for scaling
    max_abs = max(abs(h.get("gain_loss", 0)) for h in holdings) if holdings else 1
    if max_abs == 0:
        max_abs = 1

    bar_scale = half_width / max_abs

    # Sort by gain_loss (best to worst)
    sorted_holdings = sorted(holdings, key=lambda x: x.get("gain_loss", 0), reverse=True)

    for h in sorted_holdings:
        symbol = h.get("symbol", "N/A")
        gl = h.get("gain_loss", 0)
        gl_pct = h.get("gain_loss_percent", 0)
        value = h.get("current_value", 0)

        # Calculate bar length
        bar_len = int(abs(gl) * bar_scale)
        bar_len = max(bar_len, 1)

        # Format the label
        marker = "+" if gl >= 0 else "-"
        label = f"{marker}${abs(gl):,.2f} ({marker}{abs(gl_pct):.1f}%)"

        if gl >= 0:
            # Gain: center → right (green)
            left_pad = half_width
            bar = f"{GREEN}{'█' * bar_len}{RESET}"
            right_pad = half_width - bar_len
            line = f"  {symbol:<6} {' ' * left_pad}{bar}{' ' * right_pad}  {GREEN}{label:>22}{RESET}  ${value:>10,.2f}"
        else:
            # Loss: left → center (red)
            left_pad = half_width - bar_len
            bar = f"{RED}{'▓' * bar_len}{RESET}"
            right_pad = half_width
            line = f"  {symbol:<6} {' ' * left_pad}{bar}{' ' * right_pad}  {RED}{label:>22}{RESET}  ${value:>10,.2f}"

        lines.append(line)

    if not bars_only:
        # Center marker
        lines.append(f"  {'':6} {' ' * (half_width - 1)}|")
        lines.append(f"  {'':6} {' ' * (half_width - 4)}{'─' * 8}")

        # Footer
        lines.append("")
        lines.append("─" * (width + 55))
        total_marker = "+" if total_gl >= 0 else "-"
        total_color = GREEN if total_gl >= 0 else RED
        lines.append(f"  TOTAL COST BASIS:  ${total_cost:>14,.2f}")
        lines.append(f"  TOTAL VALUE:       ${total_value:>14,.2f}")
        lines.append(f"  TOTAL GAIN/LOSS:   {total_color}{total_marker}${abs(total_gl):>13,.2f} ({total_marker}{abs(total_gl_pct):.1f}%){RESET}")
        lines.append("─" * (width + 55))

    return "\n".join(lines)
