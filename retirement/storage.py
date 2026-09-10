"""Storage module — saves and loads holdings data to/from YAML or TOML."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


def save_to_yaml(data: dict[str, Any], filepath: str | Path) -> Path:
    """Save holdings data to YAML file."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "last_updated": datetime.now().isoformat(),
        "total_value": data.get("total_value", 0),
        "total_cost_basis": data.get("total_cost_basis", 0),
        "total_gain_loss": data.get("total_gain_loss", 0),
        "holdings": data.get("combined", []),
    }

    with open(filepath, "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False)

    return filepath


def load_from_yaml(filepath: str | Path) -> dict[str, Any]:
    """Load holdings data from YAML file."""
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"No data file found at {filepath}")

    with open(filepath) as f:
        return yaml.safe_load(f)


def save_to_toml(data: dict[str, Any], filepath: str | Path) -> Path:
    """Save holdings data to TOML file."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    try:
        import tomllib  # Python 3.11+
    except ImportError:
        pass

    try:
        import tomli_w as tomllib_write
    except ImportError:
        # Fallback: write TOML manually
        return _save_to_toml_manual(data, filepath)

    output = {
        "metadata": {
            "last_updated": datetime.now().isoformat(),
            "total_value": data.get("total_value", 0),
            "total_cost_basis": data.get("total_cost_basis", 0),
            "total_gain_loss": data.get("total_gain_loss", 0),
        },
        "holdings": data.get("combined", []),
    }

    with open(filepath, "wb") as f:
        tomllib_write.dump(output, f)

    return filepath


def _save_to_toml_manual(data: dict[str, Any], filepath: Path) -> Path:
    """Fallback TOML writer when tomli_w is not available."""
    holdings = data.get("combined", [])

    lines = [
        f'last_updated = "{datetime.now().isoformat()}"',
        f"total_value = {data.get('total_value', 0)}",
        f"total_cost_basis = {data.get('total_cost_basis', 0)}",
        f"total_gain_loss = {data.get('total_gain_loss', 0)}",
        "",
    ]

    for i, h in enumerate(holdings):
        prefix = f"holdings[{i}]"
        lines.extend([
            f"[{prefix}]",
            f'symbol = "{h["symbol"]}"',
            f'name = "{h["name"]}"',
            f"total_quantity = {h['total_quantity']}",
            f"average_cost = {h['average_cost']}",
            f"total_cost_basis = {h['total_cost_basis']}",
            f"current_price = {h['current_price']}",
            f"current_value = {h['current_value']}",
            f"gain_loss = {h['gain_loss']}",
            f"gain_loss_percent = {h['gain_loss_percent']}",
            "",
        ])

    with open(filepath, "w") as f:
        f.write("\n".join(lines))

    return filepath


def load_from_toml(filepath: str | Path) -> dict[str, Any]:
    """Load holdings data from TOML file."""
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"No data file found at {filepath}")

    try:
        import tomllib
    except ImportError:
        import tomli as tomllib

    with open(filepath, "rb") as f:
        data = tomllib.load(f)

    # Normalize to same format as YAML loader
    metadata = data.get("metadata", {})
    holdings = data.get("holdings", [])

    return {
        "last_updated": metadata.get("last_updated", ""),
        "total_value": metadata.get("total_value", 0),
        "total_cost_basis": metadata.get("total_cost_basis", 0),
        "total_gain_loss": metadata.get("total_gain_loss", 0),
        "holdings": holdings,
    }
