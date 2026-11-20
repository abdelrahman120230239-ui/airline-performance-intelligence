"""Render four PNG report previews from profile_bts.py output (requires Pillow)."""
import argparse
import json
import os
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1440, 900
INK, NAVY, MUTED, TEAL = "#172D43", "#142D46", "#52687B", "#007F78"
PURPLE, AMBER, BG, BORDER, WHITE = "#6B5AA4", "#9C5508", "#F1F5F8", "#DBE5ED", "#FFFFFF"
NAV = ["Executive", "Airlines", "Airports & routes", "Disruptions"]
FONT = Path(os.environ.get("AIRLINE_FONT_DIR", "/usr/share/fonts/truetype/dejavu"))


@lru_cache
def font(size, bold=False):
    return ImageFont.truetype(str(FONT / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")), size)


def pct(row, numerator="ontime", denominator="arr_eligible"):
    return row[numerator] / row[denominator] if row[denominator] else 0


def p(value):
    return f"{value:.2%}"


def n(value):
    return f"{value:,}"


def pp(value):
    return f"{100 * value:+.2f} pp"


def millions(value):
    return f"{value / 1_000_000:.2f}M"


class Page:
    def __init__(self, index, title, footer):
        self.image = Image.new("RGB", (W, H), BG)
        self.draw = ImageDraw.Draw(self.image)
        self.draw.rectangle((0, 0, W, 6), fill=TEAL)
        self.text(32, 34, "AIRLINE PERFORMANCE INTELLIGENCE", 14, TEAL, True)
        self.text(32, 76, title, 34, NAVY, True)
        for i, tab in enumerate(NAV):
            x = 792 + i * 155
            self.box(x, 66, 144, 44, NAVY if index == i else WHITE, None if index == i else BORDER)
            self.text(x + 72, 88, tab, 13, WHITE if index == i else INK, True, "mm")
        for i, (label, value) in enumerate([
            ("Reporting month", "2025-01, 2025-02"),
            ("Reporting carrier", "All carriers"),
            ("Scheduled origin", "All origins"),
            ("Scheduled destination", "All destinations"),
        ]):
            x = 32 + 348 * i
            self.box(x, 139, 332, 76)
            self.text(x + 15, 153, label, 13, MUTED, True)
            self.text(x + 15, 182, value, 15, INK)
            self.text(x + 310, 184, "⌄", 16, MUTED, anchor="ra")
        self.draw.line((32, 845, 1408, 845), fill=BORDER)
        self.text(32, 862, footer, 12, MUTED)
        self.text(1408, 862, "BTS TRANSTATS  /  REPORT PREVIEW", 11, MUTED, True, "ra")

    def text(self, x, y, value, size=14, color=INK, bold=False, anchor="la"):
        self.draw.text((x, y), str(value), font=font(size, bold), fill=color, anchor=anchor)

    def box(self, x, y, width, height, fill=WHITE, outline=BORDER, radius=9):
        self.draw.rounded_rectangle((x, y, x + width, y + height), radius, fill=fill, outline=outline)

    def panel(self, x, y, width, height, title, subtitle=None):
        self.box(x, y, width, height)
        self.text(x + 18, y + 17, title, 18, NAVY, True)
        if subtitle:
            self.text(x + 18, y + 43, subtitle, 12, MUTED)

    def kpis(self, items):
        width = (1376 - 12 * (len(items) - 1)) / len(items)
        for i, (label, value) in enumerate(items):
            x = int(32 + i * (width + 12))
            self.box(x, 235, int(width), 103)
            self.draw.rectangle((x + 16, 252, x + 19, 315), fill=TEAL if i < 2 else BORDER)
            self.text(x + 30, 255, label, 13, MUTED, True)
            self.text(x + 30, 278, value, 28, NAVY, True)

    def table(self, x, y, width, height, title, headers, rows, divisions,
              *, subtitle=None, row_height=24, center=()):
        self.panel(x, y, width, height, title, subtitle)
        left = x + 14
        right = x + width - 14
        grid_width = right - left
        y = y + (68 if subtitle else 50)
        edges = [left + int(grid_width * cut) for cut in divisions]
        self.box(left, y, grid_width, 30, NAVY, None, 4)
        for i, header in enumerate(headers):
            self.text(edges[i] + 9, y + 15, header, 11, WHITE, True, "lm")
        y += 30
        for idx, row in enumerate(rows):
            if idx % 2 == 0:
                self.draw.rectangle((left, y, right, y + row_height), fill=BG)
            for col, value in enumerate(row):
                if col in center:
                    self.text((edges[col] + edges[col + 1]) / 2, y + row_height / 2,
                              value, 12, INK, False, "mm")
                else:
                    self.text(edges[col] + 9, y + row_height / 2, value, 12, INK, col == 0, "lm")
            y += row_height
        self.draw.line((left, y, right, y), fill=BORDER)

    def bars(self, x, y, width, height, title, series, maximum, format_value, color=TEAL, *,
             subtitle=None, label_width=86):
        self.panel(x, y, width, height, title, subtitle)
        top = y + (68 if subtitle else 52)
        base = y + height - 24
        left = x + label_width + 20
        track = x + width - 94 - left
        row = (base - top) / len(series)
        for i, (label, value) in enumerate(series):
            mid = top + row * (i + 0.5)
            high = min(9, row * 0.28)
            self.text(x + 18, mid, label, 12, MUTED, True, "lm")
            self.box(left, int(mid - high), track, int(high * 2), BG, None, 4)
            if value:
                self.box(left, int(mid - high), max(3, min(track, int(track * value / maximum))),
                         int(high * 2), color, None, 4)
            self.text(x + width - 18, mid, format_value(value), 13, INK, True, "rm")

    def columns(self, x, y, width, height, title, series):
        self.panel(x, y, width, height, title, "Share of comparable arrivals arriving less than 15 minutes late")
        top, bottom = y + 98, y + height - 58
        left, right = x + 70, x + width - 28
        for t in (0, 0.25, 0.5, 0.75, 1):
            axis = bottom - (bottom - top) * t
            self.draw.line((left, axis, right, axis), fill=BORDER)
            self.text(left - 13, axis, f"{t:.0%}", 12, MUTED, anchor="rm")
        step = (right - left) / len(series)
        for i, (label, value) in enumerate(series):
            center = left + step * (i + 0.5)
            bar_top = bottom - (bottom - top) * value
            self.box(int(center - 55), int(bar_top), 110, int(bottom - bar_top), TEAL, None, 6)
            self.text(center, bar_top - 16, p(value), 16, NAVY, True, "mm")
            self.text(center, bottom + 23, label, 13, INK, True, "mm")

    def save(self, path):
        self.image.save(path, optimize=True)


def render(aggregates, destination):
    months = aggregates["month"]
    year = aggregates["year"]["2025"]
    selection = [("2025-01", "Jan 2025"), ("2025-02", "Feb 2025")]
    values = [(label, months[key]) for key, label in selection]
    leap = aggregates["date"]["2024-02-29"]
    prev = aggregates["year"]["2024"]
    network = pct(year)
    prior_matched = (prev["ontime"] - leap["ontime"]) / (prev["arr_eligible"] - leap["arr_eligible"])
    page = Page(0, "Executive Overview",
                "Arrival OTP uses comparable arrivals. Cancellation and diversion rates use scheduled flights.")
    page.kpis([("Scheduled flights", n(year["scheduled"])), ("On-time arrivals", p(network)),
               ("Cancellation rate", p(pct(year, "cancelled", "scheduled"))),
               ("Diversion rate", p(pct(year, "diverted", "scheduled"))),
               ("Arrival OTP YoY", pp(network - prior_matched))])
    page.columns(32, 359, 765, 470, "Arrival reliability | 2025-01 · 2025-02", [(label, pct(row)) for label, row in values])
    monthly = []
    for key, label in selection:
        row = months[key]
        prior = months[key.replace("2025", "2024")]
        omit = leap if key.endswith("02") else {"ontime": 0, "arr_eligible": 0}
        prior_otp = (prior["ontime"] - omit["ontime"]) / (prior["arr_eligible"] - omit["arr_eligible"])
        monthly.append([label, n(row["arr_eligible"]), p(pct(row)), p(pct(row, "cancelled", "scheduled")),
                        p(pct(row, "diverted", "scheduled")), pp(pct(row) - prior_otp)])
    page.table(815, 359, 593, 284, "Monthly scorecard",
               ["Month", "Comparable", "Arrival OTP", "Cancelled", "Diverted", "YoY"],
               monthly, [0, .17, .36, .53, .69, .84, 1], subtitle="YoY uses exactly matched dates", row_height=42)
    page.panel(815, 660, 593, 169, "Reported coverage")
    page.text(833, 713, f'{n(year["arr_eligible"])} comparable arrivals', 22, NAVY, True)
    page.text(833, 750, f'{n(year["cancelled"])} cancellations  ·  {n(year["diverted"])} diversions', 14, MUTED)
    page.save(destination / "01-executive-overview.png")

    def year_filter(key):
        return [(k.split("|", 1)[1], v) for k, v in aggregates[key + "_year"].items() if k.startswith("2025|")]

    carriers = sorted(year_filter("carrier"), key=lambda item: -pct(item[1]))
    page = Page(1, "Airline Benchmarking",
                "Carrier rank requires 1,000 comparable arrivals. Network OTP is weighted across permitted carriers.")
    page.kpis([("Scheduled flights", n(year["scheduled"])), ("Comparable arrivals", n(year["arr_eligible"])),
               ("On-time arrivals", p(network)), ("Network arrival OTP", p(network))])
    page.bars(32, 359, 499, 470, "Carrier comparison | 2025-01 · 2025-02", [(code, pct(v)) for code, v in carriers],
              1, p, subtitle="Arrival OTP by reporting carrier", label_width=49)
    rows = [[code, n(v["arr_eligible"]), p(pct(v)), pp(pct(v) - network), p(pct(v, "cancelled", "scheduled")), i]
            for i, (code, v) in enumerate(carriers, 1)]
    page.table(549, 359, 859, 470, "Carrier scorecard",
               ["Carrier", "Comparable", "Arrival OTP", "Network gap", "Cancelled", "Rank"], rows,
               [0, .16, .34, .51, .70, .88, 1], row_height=26.5)
    page.save(destination / "02-airline-benchmarking.png")

    page = Page(2, "Airport and Route Analysis",
                "Select a directional route to open its flight records. Route rank requires 500 comparable arrivals.")
    for key, x, width, tone in [("origin", 32, 688, TEAL), ("destination", 738, 670, PURPLE)]:
        places = sorted(year_filter(key), key=lambda item: -item[1]["late_minutes"])[:6]
        page.bars(x, 235, width, 265, f"{key.title()} airports by late-arrival minutes",
                  [(code, v["late_minutes"]) for code, v in places], 900_000, n, tone,
                  label_width=50)
    routes = sorted(year_filter("route"), key=lambda item: -item[1]["late_minutes"])[:15]
    page.box(1222, 507, 186, 30, NAVY, None)
    page.text(1315, 522, "Open flight records", 12, WHITE, True, "mm")
    rows = []
    rank = 0
    for route, v in routes[:8]:
        if v["arr_eligible"] >= 500:
            rank += 1
        rows.append([route, n(v["scheduled"]), n(v["arr_eligible"]), p(pct(v)), n(v["cancelled"]),
                     n(v["late_minutes"]), rank if v["arr_eligible"] >= 500 else "—"])
    page.table(32, 542, 1376, 287, "Directional routes | 2025-01 · 2025-02",
               ["Route", "Scheduled", "Comparable", "Arrival OTP", "Cancelled", "Late minutes", "Burden rank"],
               rows, [0, .20, .33, .47, .61, .74, .88, 1], row_height=24)
    page.save(destination / "03-airport-and-route-analysis.png")

    page = Page(3, "Delay and Cancellation Investigation",
                "Delay minutes and cancellation reasons are reported by carriers using BTS categories.")
    page.kpis([("Delayed arrivals", n(year["late"])), ("Arrivals 60+ minutes late", n(year["late60"])),
               ("Avg min per late arrival", f'{year["late_minutes"] / year["late"]:.1f}'),
               ("Cancelled flights", n(year["cancelled"])),
               ("Reported cause coverage", p(pct(year, "cause_covered", "late")))])
    for i, label in enumerate(("Chart", "Table")):
        x = 32 + 100 * i
        page.box(x, 354, 90, 31, NAVY if i == 0 else WHITE, None if i == 0 else BORDER)
        page.text(x + 45, 369, label, 13, WHITE if i == 0 else INK, True, "mm")
    attribution = [(label, year[key]) for label, key in [
        ("Late-arriving aircraft", "LateAircraftDelay"), ("Air carrier", "CarrierDelay"),
        ("National Aviation System", "NASDelay"), ("Weather", "WeatherDelay"), ("Security", "SecurityDelay")]]
    reason_names = {"A":"Air carrier", "B":"Weather", "C":"National Aviation System", "D":"Security", "?":"Unknown or missing"}
    reasons = sorted([(reason_names[k], v["cancelled"]) for k, v in year_filter("cancellation_reason")],
                     key=lambda item: -item[1])
    page.bars(32, 398, 714, 431, "Reported delay attribution | 2025-01 · 2025-02", attribution, 5_500_000,
              n, subtitle="Reported minutes on comparable arrivals delayed 15 minutes or more", label_width=195)
    page.bars(764, 398, 644, 431, "Reported cancellation reasons", reasons, 21_000,
              n, AMBER, subtitle="Cancelled segments by BTS reason code", label_width=195)
    page.save(destination / "04-delay-and-cancellation-investigation.png")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    args.destination.mkdir(exist_ok=True, parents=True)
    aggregate = json.loads(args.profile.read_text(encoding="utf-8"))["aggregates"]
    render(aggregate, args.destination)


if __name__ == "__main__":
    main()
