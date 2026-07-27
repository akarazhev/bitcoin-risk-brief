#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(REPO_ROOT / "collector"))

from app.risk import LOW_RISK_THRESHOLD, HIGH_RISK_THRESHOLD, METHODOLOGY_VERSION, RiskPoint, classify_risk
from app.risk_sources import build_csv_risk_dataset


DEFAULT_CSV_PATH = REPO_ROOT / "collector" / "btc-csv" / "btc_usd_daily.csv"
DEFAULT_OUTPUT_PATH = REPO_ROOT / "docs" / "bitcoin-risk-all-period-chart.png"
CANVAS_WIDTH = 2400
CANVAS_HEIGHT = 1600
SCALE = 2

BACKGROUND = "#0c0d0f"
SURFACE = "#15171b"
SURFACE_SOFT = "#111316"
FOREGROUND = "#f4f0e8"
MUTED = "#b2ada5"
DIM = "#8d948f"
BORDER = "#30343b"
GRID = "#242830"
LOW = "#5bd687"
LOW_FILL = "#163721"
NEUTRAL = "#f2b84b"
NEUTRAL_FILL = "#342916"
HIGH = "#ff6b5f"
HIGH_FILL = "#3a1f1f"
PRICE = "#5bd6c6"


@dataclass(frozen=True)
class ChartArea:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top


def _scaled(value: float | int) -> int:
    return int(round(float(value) * SCALE))


def _scaled_area(area: ChartArea) -> tuple[int, int, int, int]:
    return (_scaled(area.left), _scaled(area.top), _scaled(area.right), _scaled(area.bottom))


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    if bold:
        candidates = [
            "/System/Library/Fonts/SFNS.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/SFNSRounded.ttf",
            "/Library/Fonts/Arial Unicode.ttf",
        ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, _scaled(size))
        except OSError:
            continue
    return ImageFont.load_default()


def _date_label(day: date) -> str:
    return day.isoformat()


def _money(value: float) -> str:
    if value >= 1000:
        return f"${value:,.0f}"
    if value >= 1:
        return f"${value:,.2f}"
    return f"${value:.4f}"


def _risk_color(risk: float) -> str:
    state = classify_risk(risk)
    if state == "low":
        return LOW
    if state == "high":
        return HIGH
    return NEUTRAL


def _risk_state_counts(points: Iterable[RiskPoint]) -> dict[str, int]:
    counts = {"low": 0, "neutral": 0, "high": 0}
    for point in points:
        counts[classify_risk(point.risk)] += 1
    return counts


def _x_mapper(days: list[date], area: ChartArea):
    min_ord = days[0].toordinal()
    span = max(days[-1].toordinal() - min_ord, 1)

    def x_for(day: date) -> int:
        return area.left + int(round(((day.toordinal() - min_ord) / span) * area.width))

    return x_for


def _risk_y(area: ChartArea, risk: float) -> int:
    return area.bottom - int(round(max(0.0, min(1.0, risk)) * area.height))


def _price_y(area: ChartArea, price: float, min_log: float, max_log: float) -> int:
    value = math.log10(max(price, 1e-12))
    span = max(max_log - min_log, 1e-12)
    return area.bottom - int(round(((value - min_log) / span) * area.height))


def _draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: str = FOREGROUND,
    *,
    anchor: str | None = None,
) -> None:
    draw.text((_scaled(xy[0]), _scaled(xy[1])), text, font=font, fill=fill, anchor=anchor)


def _draw_line(
    draw: ImageDraw.ImageDraw,
    points: list[tuple[int, int]],
    fill: str,
    *,
    width: int = 2,
) -> None:
    if len(points) >= 2:
        draw.line([(_scaled(x), _scaled(y)) for x, y in points], fill=fill, width=_scaled(width), joint="curve")


def _draw_card(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    label: str,
    value: str,
    note: str,
    *,
    accent: str = FOREGROUND,
) -> None:
    draw.rounded_rectangle(
        tuple(_scaled(value) for value in box),
        radius=_scaled(8),
        fill=SURFACE,
        outline=BORDER,
        width=_scaled(1),
    )
    left, top, _, _ = box
    _draw_text(draw, (left + 22, top + 20), label, _font(26), DIM)
    _draw_text(draw, (left + 22, top + 60), value, _font(42, bold=True), accent)
    _draw_text(draw, (left + 22, top + 118), note, _font(23), MUTED)


def _draw_year_grid(draw: ImageDraw.ImageDraw, days: list[date], area: ChartArea, *, labels: bool = True) -> None:
    x_for = _x_mapper(days, area)
    start_year = ((days[0].year + 1) // 2) * 2
    for year in range(start_year, days[-1].year + 1, 2):
        x = x_for(date(year, 1, 1))
        draw.line(
            [(_scaled(x), _scaled(area.top)), (_scaled(x), _scaled(area.bottom))],
            fill=GRID,
            width=_scaled(1),
        )
        if labels:
            _draw_text(draw, (x, area.bottom + 16), str(year), _font(21), DIM, anchor="mt")


def _draw_risk_chart(
    draw: ImageDraw.ImageDraw,
    points: list[RiskPoint],
    area: ChartArea,
) -> None:
    days = [point.day for point in points]
    x_for = _x_mapper(days, area)

    for low, high, fill in (
        (0.0, LOW_RISK_THRESHOLD, LOW_FILL),
        (LOW_RISK_THRESHOLD, HIGH_RISK_THRESHOLD, NEUTRAL_FILL),
        (HIGH_RISK_THRESHOLD, 1.0, HIGH_FILL),
    ):
        y_top = _risk_y(area, high)
        y_bottom = _risk_y(area, low)
        draw.rectangle((_scaled(area.left), _scaled(y_top), _scaled(area.right), _scaled(y_bottom)), fill=fill)

    for tick in (0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.8, 0.9, 1.0):
        y = _risk_y(area, tick)
        draw.line(
            [(_scaled(area.left), _scaled(y)), (_scaled(area.right), _scaled(y))],
            fill=GRID if tick not in (LOW_RISK_THRESHOLD, HIGH_RISK_THRESHOLD) else BORDER,
            width=_scaled(1 if tick not in (LOW_RISK_THRESHOLD, HIGH_RISK_THRESHOLD) else 2),
        )
        _draw_text(draw, (area.left - 22, y), f"{tick:.1f}", _font(22), DIM, anchor="rm")

    _draw_year_grid(draw, days, area)

    contiguous: list[tuple[str, list[tuple[int, int]]]] = []
    current_color = _risk_color(points[0].risk)
    current_segment: list[tuple[int, int]] = []
    for point in points:
        color = _risk_color(point.risk)
        mapped = (x_for(point.day), _risk_y(area, point.risk))
        if color != current_color and current_segment:
            current_segment.append(mapped)
            contiguous.append((current_color, current_segment))
            current_segment = [mapped]
            current_color = color
        else:
            current_segment.append(mapped)
    contiguous.append((current_color, current_segment))

    for color, segment in contiguous:
        _draw_line(draw, segment, color, width=3)

    draw.rectangle(_scaled_area(area), outline=BORDER, width=_scaled(2))

    latest = points[-1]
    latest_xy = (x_for(latest.day), _risk_y(area, latest.risk))
    draw.ellipse(
        (
            _scaled(latest_xy[0] - 8),
            _scaled(latest_xy[1] - 8),
            _scaled(latest_xy[0] + 8),
            _scaled(latest_xy[1] + 8),
        ),
        fill=FOREGROUND,
        outline=_risk_color(latest.risk),
        width=_scaled(4),
    )
    _draw_text(
        draw,
        (min(latest_xy[0] - 10, area.right - 260), max(area.top + 22, latest_xy[1] - 46)),
        f"Latest {latest.risk:.3f} ({classify_risk(latest.risk)})",
        _font(24, bold=True),
        FOREGROUND,
        anchor="rt",
    )

    _draw_text(draw, (area.left, area.top - 42), "Daily risk score, full local history", _font(31, bold=True), FOREGROUND)
    _draw_text(draw, (area.right, area.top - 36), "Bands: low <0.30, neutral 0.30-0.70, high >=0.70", _font(23), MUTED, anchor="rt")


def _draw_price_chart(
    draw: ImageDraw.ImageDraw,
    points: list[RiskPoint],
    area: ChartArea,
) -> None:
    days = [point.day for point in points]
    prices = [point.price_hlc3 for point in points]
    x_for = _x_mapper(days, area)
    min_power = math.floor(math.log10(min(prices)))
    max_power = math.ceil(math.log10(max(prices)))
    min_log = float(min_power)
    max_log = float(max_power)

    for power in range(min_power, max_power + 1):
        value = 10**power
        y = _price_y(area, value, min_log, max_log)
        draw.line(
            [(_scaled(area.left), _scaled(y)), (_scaled(area.right), _scaled(y))],
            fill=GRID,
            width=_scaled(1),
        )
        _draw_text(draw, (area.left - 22, y), _money(value), _font(22), DIM, anchor="rm")

    _draw_year_grid(draw, days, area, labels=False)
    price_points = [(x_for(point.day), _price_y(area, point.price_hlc3, min_log, max_log)) for point in points]
    _draw_line(draw, price_points, PRICE, width=3)
    draw.rectangle(_scaled_area(area), outline=BORDER, width=_scaled(2))
    _draw_text(draw, (area.left, area.top - 42), "Model price context (HLC3, log scale)", _font(31, bold=True), FOREGROUND)
    _draw_text(draw, (area.right, area.top - 36), f"Latest { _money(points[-1].price_hlc3) }", _font(23), MUTED, anchor="rt")


def build_chart(csv_path: Path, output_path: Path) -> dict[str, object]:
    dataset = build_csv_risk_dataset(csv_path)
    points: list[RiskPoint] = dataset["risk_points"]
    validation = dataset["validation"]
    if not points:
        raise ValueError("No risk points available for chart export")

    latest = points[-1]
    highest = max(points, key=lambda point: point.risk)
    lowest = min(points, key=lambda point: point.risk)
    counts = _risk_state_counts(points)

    image = Image.new("RGB", (_scaled(CANVAS_WIDTH), _scaled(CANVAS_HEIGHT)), BACKGROUND)
    draw = ImageDraw.Draw(image)

    _draw_text(draw, (90, 74), "Bitcoin Risk Brief", _font(58, bold=True), FOREGROUND)
    _draw_text(draw, (90, 140), "All-period daily BTC risk chart from the local canonical dataset", _font(31), MUTED)
    _draw_text(
        draw,
        (CANVAS_WIDTH - 90, 82),
        f"{validation['covered_start'].isoformat()} -> {validation['covered_end'].isoformat()}",
        _font(30, bold=True),
        FOREGROUND,
        anchor="rt",
    )
    _draw_text(
        draw,
        (CANVAS_WIDTH - 90, 126),
        f"{len(points):,} rows | {METHODOLOGY_VERSION} | CoinMarketCap CSV",
        _font(24),
        MUTED,
        anchor="rt",
    )

    card_top = 210
    card_width = 510
    card_height = 160
    gap = 26
    _draw_card(
        draw,
        (90, card_top, 90 + card_width, card_top + card_height),
        "Latest risk",
        f"{latest.risk:.3f}",
        f"{_date_label(latest.day)} | {classify_risk(latest.risk)}",
        accent=_risk_color(latest.risk),
    )
    _draw_card(
        draw,
        (90 + (card_width + gap), card_top, 90 + (card_width + gap) * 2, card_top + card_height),
        "Highest risk",
        f"{highest.risk:.3f}",
        _date_label(highest.day),
        accent=HIGH,
    )
    _draw_card(
        draw,
        (90 + (card_width + gap) * 2, card_top, 90 + (card_width + gap) * 3, card_top + card_height),
        "Lowest risk",
        f"{lowest.risk:.3f}",
        _date_label(lowest.day),
        accent=LOW,
    )
    _draw_card(
        draw,
        (90 + (card_width + gap) * 3, card_top, CANVAS_WIDTH - 90, card_top + card_height),
        "State coverage",
        f"L {counts['low']:,} / N {counts['neutral']:,} / H {counts['high']:,}",
        "daily observations",
        accent=FOREGROUND,
    )

    risk_area = ChartArea(left=180, top=480, right=CANVAS_WIDTH - 100, bottom=1040)
    price_area = ChartArea(left=180, top=1210, right=CANVAS_WIDTH - 100, bottom=1455)
    _draw_risk_chart(draw, points, risk_area)
    _draw_price_chart(draw, points, price_area)

    footer = (
        "Generated from collector/btc-csv/btc_usd_daily.csv. "
        f"Missing dates: {validation['missing_date_count']}; invalid risk values: {validation['invalid_risk_value_count']}. "
        "Analytics output only, not financial advice."
    )
    _draw_text(draw, (90, CANVAS_HEIGHT - 58), footer, _font(23), DIM)

    image = image.resize((CANVAS_WIDTH, CANVAS_HEIGHT), Image.Resampling.LANCZOS)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, optimize=True)

    return {
        "output_path": output_path,
        "covered_start": validation["covered_start"],
        "covered_end": validation["covered_end"],
        "row_count": len(points),
        "latest_day": latest.day,
        "latest_risk": latest.risk,
        "highest_day": highest.day,
        "highest_risk": highest.risk,
        "lowest_day": lowest.day,
        "lowest_risk": lowest.risk,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a full-period BTC risk chart PNG from the canonical CSV.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH, help="Path to BTC USD daily CSV.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="Output PNG path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = build_chart(args.csv, args.output)
    print(f"Wrote {summary['output_path']}")
    print(
        "Coverage: "
        f"{summary['covered_start'].isoformat()} -> {summary['covered_end'].isoformat()} "
        f"({summary['row_count']:,} rows)"
    )
    print(f"Latest risk: {summary['latest_risk']:.4f} on {summary['latest_day'].isoformat()}")
    print(f"Highest risk: {summary['highest_risk']:.4f} on {summary['highest_day'].isoformat()}")
    print(f"Lowest risk: {summary['lowest_risk']:.4f} on {summary['lowest_day'].isoformat()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
