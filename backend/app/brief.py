from __future__ import annotations

from typing import Any


SUPPORTED_BRIEF_LOCALES = ("en", "ru", "zh", "de", "fr", "es", "ar")

RISK_COPY: dict[str, dict[str, tuple[str, str, str]]] = {
    "en": {
        "high": (
            "Risk is elevated. The model is flagging a stretched BTC regime.",
            "Avoid treating upside momentum as a fresh low-risk entry without confirmation.",
            "Confirm with liquidity, trend quality, and whether risk cools while price holds structure.",
        ),
        "low": (
            "Risk is low. BTC is closer to a discounted or washed-out regime.",
            "Avoid treating the low-risk zone as an immediate reversal signal.",
            "Confirm with improving trend, liquidity, and reduced forced-selling pressure.",
        ),
        "neutral": (
            "Risk is neutral. BTC is not showing an extreme risk reading right now.",
            "Avoid forcing a directional conclusion from the risk score alone.",
            "Confirm with trend, liquidity, and market rotation before drawing conclusions from this signal.",
        ),
    },
    "ru": {
        "high": (
            "Риск повышен. Модель видит перегретый режим BTC.",
            "Не стоит считать импульс вверх новой низкорисковой точкой входа без подтверждения.",
            "Проверьте ликвидность, качество тренда и снижается ли риск при удержании структуры цены.",
        ),
        "low": (
            "Риск низкий. BTC ближе к зоне дисконта или капитуляции.",
            "Не стоит считать низкий риск мгновенным сигналом разворота.",
            "Проверьте восстановление тренда, ликвидность и снижение давления продавцов.",
        ),
        "neutral": (
            "Риск нейтральный. Сейчас нет экстремального риск-сигнала по BTC.",
            "Не стоит делать направленный вывод только по риск-метрике.",
            "Проверьте тренд, ликвидность и рыночную ротацию, прежде чем делать выводы по этому сигналу.",
        ),
    },
    "zh": {
        "high": (
            "风险偏高。模型正在标记 BTC 处于偏拉伸的状态。",
            "避免在没有确认的情况下，把上涨动能视为新的低风险入场点。",
            "请结合流动性、趋势质量，以及价格保持结构时风险是否降温来确认。",
        ),
        "low": (
            "风险偏低。BTC 更接近折价或被充分释放压力的状态。",
            "避免把低风险区域直接理解为立即反转信号。",
            "请结合趋势改善、流动性和强制卖压下降来确认。",
        ),
        "neutral": (
            "风险中性。BTC 当前没有显示极端风险读数。",
            "避免仅凭风险分数得出方向性结论。",
            "在根据该信号得出结论前，请结合趋势、流动性和市场轮动确认。",
        ),
    },
    "de": {
        "high": (
            "Das Risiko ist erhöht. Das Modell markiert ein überdehntes BTC-Regime.",
            "Behandeln Sie Aufwärtsmomentum ohne Bestätigung nicht als neuen risikoarmen Einstieg.",
            "Prüfen Sie Liquidität, Trendqualität und ob das Risiko abkühlt, während der Preis seine Struktur hält.",
        ),
        "low": (
            "Das Risiko ist niedrig. BTC liegt näher an einem rabattierten oder ausgewaschenen Regime.",
            "Behandeln Sie die Niedrigrisiko-Zone nicht als sofortiges Umkehrsignal.",
            "Prüfen Sie eine Verbesserung des Trends, Liquidität und nachlassenden Verkaufsdruck.",
        ),
        "neutral": (
            "Das Risiko ist neutral. BTC zeigt derzeit keinen extremen Risikowert.",
            "Leiten Sie aus dem Risikoscore allein keine Richtungsaussage ab.",
            "Prüfen Sie Trend, Liquidität und Marktrotation, bevor Sie aus diesem Signal Schlussfolgerungen ziehen.",
        ),
    },
    "fr": {
        "high": (
            "Le risque est élevé. Le modèle signale un régime BTC étiré.",
            "Évitez de traiter la dynamique haussière comme une nouvelle entrée à faible risque sans confirmation.",
            "Confirmez avec la liquidité, la qualité de la tendance et le refroidissement du risque si le prix tient sa structure.",
        ),
        "low": (
            "Le risque est faible. BTC est plus proche d’un régime décoté ou purgé.",
            "Évitez de considérer la zone de faible risque comme un signal de retournement immédiat.",
            "Confirmez avec une amélioration de la tendance, la liquidité et une baisse de la pression vendeuse forcée.",
        ),
        "neutral": (
            "Le risque est neutre. BTC ne montre pas de lecture de risque extrême pour le moment.",
            "Évitez de tirer une conclusion directionnelle du seul score de risque.",
            "Confirmez avec la tendance, la liquidité et la rotation de marché avant de tirer des conclusions de ce signal.",
        ),
    },
    "es": {
        "high": (
            "El riesgo es elevado. El modelo marca un régimen de BTC extendido.",
            "Evita tratar el impulso alcista como una nueva entrada de bajo riesgo sin confirmación.",
            "Confirma con liquidez, calidad de tendencia y si el riesgo se enfría mientras el precio mantiene estructura.",
        ),
        "low": (
            "El riesgo es bajo. BTC está más cerca de un régimen descontado o depurado.",
            "Evita interpretar la zona de bajo riesgo como una señal inmediata de reversión.",
            "Confirma con mejora de tendencia, liquidez y menor presión de venta forzada.",
        ),
        "neutral": (
            "El riesgo es neutral. BTC no muestra ahora una lectura de riesgo extrema.",
            "Evita forzar una conclusión direccional solo a partir de la puntuación de riesgo.",
            "Confirma con tendencia, liquidez y rotación de mercado antes de sacar conclusiones de esta señal.",
        ),
    },
    "ar": {
        "high": (
            "المخاطر مرتفعة. يشير النموذج إلى أن وضع BTC ممتد.",
            "تجنب اعتبار الزخم الصاعد نقطة دخول منخفضة المخاطر من دون تأكيد.",
            "أكد ذلك عبر السيولة وجودة الاتجاه وما إذا كانت المخاطر تهدأ بينما يحافظ السعر على هيكله.",
        ),
        "low": (
            "المخاطر منخفضة. BTC أقرب إلى حالة خصم أو ضغط بيعي مستنفد.",
            "تجنب اعتبار منطقة المخاطر المنخفضة إشارة انعكاس فورية.",
            "أكد ذلك عبر تحسن الاتجاه والسيولة وتراجع ضغط البيع القسري.",
        ),
        "neutral": (
            "المخاطر محايدة. لا يظهر BTC قراءة مخاطر متطرفة الآن.",
            "تجنب استخلاص نتيجة اتجاهية من درجة المخاطر وحدها.",
            "أكد ذلك عبر الاتجاه والسيولة ودوران السوق قبل استخلاص استنتاجات من هذه الإشارة.",
        ),
    },
}


def _risk_copy(locale: str, state: str) -> tuple[str, str, str]:
    locale_copy = RISK_COPY.get(locale, RISK_COPY["en"])
    return locale_copy.get(state, locale_copy["neutral"])


def _change_copy(locale: str, delta_risk: float) -> str:
    if abs(delta_risk) < 0.01:
        return {
            "en": "Risk is broadly unchanged from the previous observation.",
            "ru": "Риск почти не изменился относительно предыдущего наблюдения.",
            "zh": "风险与上一条观测基本持平。",
            "de": "Das Risiko ist gegenüber der vorherigen Beobachtung weitgehend unverändert.",
            "fr": "Le risque est globalement inchangé par rapport à l’observation précédente.",
            "es": "El riesgo se mantiene prácticamente sin cambios frente a la observación anterior.",
            "ar": "المخاطر شبه مستقرة مقارنة بالملاحظة السابقة.",
        }[locale]
    if delta_risk > 0:
        return {
            "en": f"Risk increased by {delta_risk:.2f} points.",
            "ru": f"Риск вырос на {delta_risk:.2f} пункта.",
            "zh": f"风险上升 {delta_risk:.2f} 点。",
            "de": f"Das Risiko stieg um {delta_risk:.2f} Punkte.",
            "fr": f"Le risque a augmenté de {delta_risk:.2f} point.",
            "es": f"El riesgo subió {delta_risk:.2f} puntos.",
            "ar": f"ارتفعت المخاطر بمقدار {delta_risk:.2f} نقطة.",
        }[locale]
    cooled = abs(delta_risk)
    return {
        "en": f"Risk cooled by {cooled:.2f} points.",
        "ru": f"Риск снизился на {cooled:.2f} пункта.",
        "zh": f"风险下降 {cooled:.2f} 点。",
        "de": f"Risiko ging zurück um {cooled:.2f} Punkte.",
        "fr": f"Le risque a reculé de {cooled:.2f} point.",
        "es": f"El riesgo bajó {cooled:.2f} puntos.",
        "ar": f"انخفضت المخاطر بمقدار {cooled:.2f} نقطة.",
    }[locale]


def build_brief(latest: dict[str, Any], previous: dict[str, Any] | None = None) -> dict[str, Any]:
    latest_risk = float(latest["risk"])
    previous_risk = float(previous["risk"]) if previous else latest_risk
    delta_risk = latest_risk - previous_risk
    state = str(latest.get("risk_state") or "neutral")

    sections = {}
    for locale in SUPPORTED_BRIEF_LOCALES:
        summary, avoid, confirm = _risk_copy(locale, state)
        sections[locale] = {
            "summary": summary,
            "what_changed": _change_copy(locale, delta_risk),
            "avoid_now": avoid,
            "confirm_next": confirm,
        }

    return {
        "snapshot_version": "bitcoin-risk-brief-v1",
        "as_of": latest["timestamp"],
        "risk": latest_risk,
        "risk_state": state,
        "price_usd": float(latest["price_usd"]),
        "delta_risk": delta_risk,
        "sections": sections,
    }
