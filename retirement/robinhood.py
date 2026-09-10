"""Robinhood API wrapper — fetches positions from Traditional and Roth IRAs."""

from __future__ import annotations

import os
import sys
from typing import Any


def _import_robinhood():
    """Lazy import robin_stocks so chart/storage work without it installed."""
    try:
        import robin_stocks.robinhood as r
        import robin_stocks.robinhood.urls as urls
        import robin_stocks.robinhood.helper as helper
        return r, urls, helper
    except ImportError:
        print("ERROR: robin_stocks not installed. Run: pip install robin_stocks")
        sys.exit(1)


def login() -> bool:
    """Authenticate with Robinhood. Supports TOTP if enabled."""
    r, _, _ = _import_robinhood()
    username = os.getenv("ROBINHOOD_USERNAME")
    password = os.getenv("ROBINHOOD_PASSWORD")
    totp = os.getenv("ROBINHOOD_TOTP")

    if not username or not password:
        print("ERROR: Set ROBINHOOD_USERNAME and ROBINHOOD_PASSWORD in .env")
        return False

    try:
        if totp:
            r.login(username, password, mfa_code=totp)
        else:
            r.login(username, password)
        return True
    except Exception as e:
        print(f"Login failed: {e}")
        return False


def logout() -> None:
    """Log out of Robinhood."""
    try:
        r, _, _ = _import_robinhood()
        r.logout()
    except Exception:
        pass


def get_ira_accounts() -> list[dict]:
    """Discover Traditional and Roth IRA accounts."""
    r, urls, helper = _import_robinhood()
    ira_accounts = []
    try:
        acct_url = urls.account_profile_url()
        all_accounts = helper.request_get(acct_url, dataType='pagination')

        if all_accounts:
            for acct in all_accounts:
                acct_type = acct.get("type", "").lower()
                if acct_type in ("roth", "traditional"):
                    ira_accounts.append({
                        "type": acct_type,
                        "display_type": "Traditional IRA" if acct_type == "traditional" else "Roth IRA",
                        "account_number": acct.get("account_number", ""),
                    })
    except Exception as e:
        print(f"Error discovering IRA accounts: {e}")

    return ira_accounts


def get_positions(account_number: str) -> list[dict]:
    """Fetch open positions for a specific account."""
    r, _, _ = _import_robinhood()
    positions = []
    try:
        raw_positions = r.get_open_stock_positions(account_number=account_number)
        for pos in raw_positions:
            quantity = float(pos.get("quantity", 0))
            if quantity <= 0:
                continue

            instrument_url = pos.get("instrument", "")
            symbol = "N/A"
            name = "N/A"

            try:
                import requests
                resp = requests.get(instrument_url, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200:
                    inst = resp.json()
                    symbol = inst.get("symbol", "N/A")
                    name = inst.get("name", "N/A")
            except Exception:
                pass

            positions.append({
                "symbol": symbol,
                "name": name,
                "quantity": quantity,
                "average_buy_price": float(pos.get("average_buy_price", 0)),
            })
    except Exception as e:
        print(f"  Error fetching positions for {account_number}: {e}")

    return positions


def get_current_prices(symbols: list[str]) -> dict[str, float]:
    """Fetch current market prices for a list of symbols."""
    r, _, _ = _import_robinhood()
    prices = {}
    for symbol in symbols:
        try:
            price = r.get_latest_price(symbol)
            if price and len(price) > 0:
                prices[symbol] = float(price[0])
        except Exception:
            prices[symbol] = 0.0
    return prices


def fetch_ira_holdings() -> dict[str, Any]:
    """Fetch and combine holdings from all IRAs."""
    if not login():
        return {}

    try:
        ira_accounts = get_ira_accounts()
        if not ira_accounts:
            print("No IRA accounts found.")
            return {}

        print(f"Found {len(ira_accounts)} IRA account(s):")
        for acct in ira_accounts:
            print(f"  • {acct['display_type']} — {acct['account_number']}")
        print()

        all_holdings = {}  # symbol -> combined data
        account_details = {}

        for acct in ira_accounts:
            positions = get_positions(acct["account_number"])
            account_details[acct["type"]] = {
                "display_type": acct["display_type"],
                "account_number": acct["account_number"],
                "holdings": positions,
            }

            for pos in positions:
                symbol = pos["symbol"]
                if symbol not in all_holdings:
                    all_holdings[symbol] = {
                        "symbol": symbol,
                        "name": pos["name"],
                        "total_quantity": 0.0,
                        "total_cost_basis": 0.0,
                    }
                all_holdings[symbol]["total_quantity"] += pos["quantity"]
                all_holdings[symbol]["total_cost_basis"] += pos["quantity"] * pos["average_buy_price"]

        # Fetch current prices for all symbols
        symbols = list(all_holdings.keys())
        print(f"Fetching current prices for {len(symbols)} symbols...")
        prices = get_current_prices(symbols)

        # Calculate combined metrics
        combined = []
        for symbol, data in all_holdings.items():
            avg_cost = data["total_cost_basis"] / data["total_quantity"] if data["total_quantity"] > 0 else 0
            current_price = prices.get(symbol, 0.0)
            current_value = data["total_quantity"] * current_price
            gain_loss = current_value - data["total_cost_basis"]
            gain_loss_percent = (gain_loss / data["total_cost_basis"] * 100) if data["total_cost_basis"] > 0 else 0

            combined.append({
                "symbol": symbol,
                "name": data["name"],
                "total_quantity": round(data["total_quantity"], 4),
                "average_cost": round(avg_cost, 2),
                "total_cost_basis": round(data["total_cost_basis"], 2),
                "current_price": round(current_price, 2),
                "current_value": round(current_value, 2),
                "gain_loss": round(gain_loss, 2),
                "gain_loss_percent": round(gain_loss_percent, 2),
            })

        # Sort by current value descending
        combined.sort(key=lambda x: x["current_value"], reverse=True)

        return {
            "accounts": account_details,
            "combined": combined,
            "total_value": round(sum(h["current_value"] for h in combined), 2),
            "total_cost_basis": round(sum(h["total_cost_basis"] for h in combined), 2),
            "total_gain_loss": round(sum(h["gain_loss"] for h in combined), 2),
        }
    finally:
        logout()
