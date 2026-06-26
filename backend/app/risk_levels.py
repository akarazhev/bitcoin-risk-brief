from __future__ import annotations

import math
from typing import Any


def build_risk_levels(latest: dict[str, Any]) -> list[dict[str, float]]:
    current_price = float(latest["price_usd"])
    current_risk = float(latest["risk"])
    rows: list[dict[str, float]] = []
    for step in range(0, 21):
        target_risk = step / 20
        multiplier = math.exp((target_risk - current_risk) * 2.2)
        rows.append({"risk": round(target_risk, 2), "price_usd": round(current_price * multiplier, 2)})
    return rows
