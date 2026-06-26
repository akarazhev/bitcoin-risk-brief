from __future__ import annotations

from typing import Any


def _risk_copy_en(state: str) -> tuple[str, str, str]:
    if state == "high":
        return (
            "Risk is elevated. The model is flagging a stretched BTC regime.",
            "Avoid treating upside momentum as a fresh low-risk entry without confirmation.",
            "Confirm with dominance, liquidity, and whether risk cools while price holds trend.",
        )
    if state == "low":
        return (
            "Risk is low. BTC is closer to a discounted or washed-out regime.",
            "Avoid assuming the low-risk zone is an immediate reversal signal.",
            "Confirm with improving trend, liquidity, and reduced forced-selling pressure.",
        )
    return (
        "Risk is neutral. BTC is not showing an extreme risk reading right now.",
        "Avoid forcing a directional conclusion from the risk score alone.",
        "Confirm with trend, liquidity, and rotation before changing exposure.",
    )


def _risk_copy_ru(state: str) -> tuple[str, str, str]:
    if state == "high":
        return (
            "Риск повышен. Модель видит перегретый режим BTC.",
            "Не стоит считать импульс вверх свежей низкорисковой точкой входа без подтверждения.",
            "Проверь доминацию, ликвидность и снижается ли риск при удержании тренда.",
        )
    if state == "low":
        return (
            "Риск низкий. BTC ближе к зоне дисконта или капитуляции.",
            "Не стоит считать низкий риск мгновенным сигналом разворота.",
            "Проверь восстановление тренда, ликвидность и снижение давления продавцов.",
        )
    return (
        "Риск нейтральный. Сейчас нет экстремального риск-сигнала по BTC.",
        "Не стоит делать направленный вывод только по риск-метрике.",
        "Проверь тренд, ликвидность и ротацию перед изменением экспозиции.",
    )


def build_brief(latest: dict[str, Any], previous: dict[str, Any] | None = None) -> dict[str, Any]:
    latest_risk = float(latest["risk"])
    previous_risk = float(previous["risk"]) if previous else latest_risk
    delta_risk = latest_risk - previous_risk
    state = str(latest.get("risk_state") or "neutral")
    en_summary, en_avoid, en_confirm = _risk_copy_en(state)
    ru_summary, ru_avoid, ru_confirm = _risk_copy_ru(state)

    if abs(delta_risk) < 0.01:
        change_en = "Risk is broadly unchanged from the previous observation."
        change_ru = "Риск почти не изменился относительно предыдущего наблюдения."
    elif delta_risk > 0:
        change_en = f"Risk increased by {delta_risk:.2f} points."
        change_ru = f"Риск вырос на {delta_risk:.2f} пункта."
    else:
        change_en = f"Risk cooled by {abs(delta_risk):.2f} points."
        change_ru = f"Риск снизился на {abs(delta_risk):.2f} пункта."

    return {
        "snapshot_version": "bitcoin-risk-brief-v1",
        "as_of": latest["timestamp"],
        "risk": latest_risk,
        "risk_state": state,
        "price_usd": float(latest["price_usd"]),
        "delta_risk": delta_risk,
        "sections": {
            "en": {
                "summary": en_summary,
                "what_changed": change_en,
                "avoid_now": en_avoid,
                "confirm_next": en_confirm,
            },
            "ru": {
                "summary": ru_summary,
                "what_changed": change_ru,
                "avoid_now": ru_avoid,
                "confirm_next": ru_confirm,
            },
        },
    }
