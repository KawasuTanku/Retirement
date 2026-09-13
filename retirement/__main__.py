"""CLI entry point for Retirement portfolio tracker."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    tankuos_dir = Path.home() / "TankuOS" / "Apps" / "Retirement" / "configs" / ".env"
    if tankuos_dir.is_file():
        # Running inside TankuOS: load only our own .env, never CWD
        load_dotenv(tankuos_dir)
    else:
        # Legacy/manual install: load .env from CWD
        load_dotenv()
except ImportError:
    pass

from retirement.robinhood import fetch_ira_holdings
from retirement.storage import (
    load_from_toml,
    load_from_yaml,
    save_to_toml,
    save_to_yaml,
)
from retirement.chart import render_bar_chart, render_rebalance


def main():
    parser = argparse.ArgumentParser(
        description="Retirement portfolio tracker — fetch IRAs and view gain/loss"
    )
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="Fetch latest holdings from Robinhood IRAs",
    )
    parser.add_argument(
        "--format",
        choices=["yaml", "toml"],
        default="yaml",
        help="Storage format (default: yaml)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/holdings",
        help="Output file path without extension (default: data/holdings)",
    )
    parser.add_argument(
        "--load",
        type=str,
        default=None,
        help="Load data from specific file instead of default",
    )
    parser.add_argument(
        "--chart-width",
        type=int,
        default=60,
        help="Width of the bar chart in characters (default: 60)",
    )
    parser.add_argument(
        "--bars-only",
        action="store_true",
        help="Show only the bars without header, footer, or summary",
    )
    parser.add_argument(
        "--rebalance",
        action="store_true",
        help="Show rebalance analysis vs target allocation",
    )

    args = parser.parse_args()

    # Fetch data from Robinhood
    if args.fetch:
        print("Fetching IRA holdings from Robinhood...\n")
        data = fetch_ira_holdings()

        if not data:
            print("Failed to fetch data.")
            sys.exit(1)

        # Save to file
        output_base = Path(args.output)

        if args.format == "yaml":
            output_path = output_base.with_suffix(".yaml")
            save_to_yaml(data, output_path)
        else:
            output_path = output_base.with_suffix(".toml")
            save_to_toml(data, output_path)

        print(f"\nData saved to {output_path}")

        # Display rebalance analysis
        if args.rebalance:
            print(render_rebalance(data, width=args.chart_width))
            return

        # Display chart
        print()
        print(render_bar_chart(data, width=args.chart_width, bars_only=args.bars_only))
        return

    # Load existing data
    if args.load:
        filepath = Path(args.load)
    else:
        # Try default paths
        yaml_path = Path(args.output).with_suffix(".yaml")
        toml_path = Path(args.output).with_suffix(".toml")

        if yaml_path.exists():
            filepath = yaml_path
        elif toml_path.exists():
            filepath = toml_path
        else:
            print("No data file found. Run with --fetch first.")
            sys.exit(1)

    # Load based on extension
    if filepath.suffix == ".yaml" or filepath.suffix == ".yml":
        data = load_from_yaml(filepath)
    elif filepath.suffix == ".toml":
        data = load_from_toml(filepath)
    else:
        print(f"Unsupported file format: {filepath.suffix}")
        sys.exit(1)

    # Display rebalance analysis
    if args.rebalance:
        print(render_rebalance(data, width=args.chart_width))
        return

    # Display chart
    print(render_bar_chart(data, width=args.chart_width, bars_only=args.bars_only))


if __name__ == "__main__":
    main()
