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


# Default target allocation
DEFAULT_TARGETS = {
    "VTI": 80,
    "SCHH": 10,
    "BND": 10,
}


def render_rebalance(
    data: dict[str, Any],
    targets: dict[str, int] | None = None,
    width: int = 70,
) -> str:
    """Render rebalance analysis showing actual vs target allocation.

    Shows drift from target and suggested trades to rebalance.
    """
    if targets is None:
        targets = DEFAULT_TARGETS

    holdings = data.get("holdings", []) or data.get("combined", [])
    if not holdings:
        return "No holdings data available."

    total_value = sum(h.get("current_value", 0) for h in holdings)
    if total_value == 0:
        return "Total portfolio value is zero."

    lines = []
    lines.append("=" * (width + 55))
    lines.append(f"  {BOLD}REBALANCE ANALYSIS — Actual vs Target{RESET}")
    lines.append("=" * (width + 55))
    lines.append("")

    # Calculate actual percentages and drift
    analysis = []
    for h in holdings:
        symbol = h.get("symbol", "N/A")
        value = h.get("current_value", 0)
        actual_pct = (value / total_value) * 100
        target_pct = targets.get(symbol, 0)
        drift = actual_pct - target_pct
        drift_value = (drift / 100) * total_value
        analysis.append({
            "symbol": symbol,
            "value": value,
            "actual_pct": actual_pct,
            "target_pct": target_pct,
            "drift": drift,
            "drift_value": drift_value,
        })

    # Sort by drift (most underweight first)
    analysis.sort(key=lambda x: x["drift"])

    # Header
    lines.append(f"  {'Symbol':<8} {'Value':>14} {'Actual':>8} {'Target':>8} {'Drift':>8}  {'Trade':>14}")
    lines.append(f"  {'─' * 8} {'─' * 14} {'─' * 8} {'─' * 8} {'─' * 8}  {'─' * 14}")

    for a in analysis:
        symbol = a["symbol"]
        value = a["value"]
        actual = a["actual_pct"]
        target = a["target_pct"]
        drift = a["drift"]
        drift_value = a["drift_value"]

        # Color code drift
        if abs(drift) < 1:
            color = DIM
            status = "OK"
        elif drift > 0:
            color = GREEN
            status = "SELL"
        else:
            color = RED
            status = "BUY"

        # Format trade suggestion
        if abs(drift) < 1:
            trade_str = "—"
        else:
            trade_str = f"{status} ${abs(drift_value):,.0f}"

        line = f"  {symbol:<8} ${value:>13,.2f} {actual:>7.1f}% {target:>7.0f}% {color}{drift:>+7.1f}%{RESET}  {color}{trade_str:>14}{RESET}"
        lines.append(line)

    # Summary
    lines.append("")
    lines.append("─" * (width + 55))
    lines.append(f"  TOTAL PORTFOLIO VALUE: ${total_value:>14,.2f}")
    lines.append("─" * (width + 55))

    # Show target allocation summary
    lines.append("")
    lines.append(f"  {BOLD}Target Allocation:{RESET}")
    for sym, pct in targets.items():
        target_value = (pct / 100) * total_value
        lines.append(f"    {sym}: {pct}% (${target_value:,.0f})")

    return "\n".join(lines)
