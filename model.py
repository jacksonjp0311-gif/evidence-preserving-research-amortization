#!/usr/bin/env python3
'''Reproduce EPRA illustrative cost arithmetic, sensitivity CSV, and SVG figures.

All values are synthetic unit assumptions, not measured costs or energy.
Uses only Python's standard library. Example: python model.py --output-dir .
'''

from __future__ import annotations
import argparse
import csv
import math
from pathlib import Path

B = 180.0
H = 45.0
M = 190.0
K = 44_000.0
N = 2_000
P0 = 0.70
GPU_BASE = 120.0
GPU_HIT = 25.0
GPU_FALLBACK = 125.0
GPU_FIXED = 10_000.0


def estimate(p: float) -> dict[str, float | int | None]:
    q = p * H + (1.0 - p) * M
    delta = B - q
    base = N * B
    amortized = K + N * q
    threshold = math.floor(K / delta) + 1 if delta > 0 else None
    return {
        "p": p,
        "cost_per_query": q,
        "delta_per_query": delta,
        "break_even_requests_strict": threshold,
        "baseline_cost_at_N": base,
        "epra_cost_at_N": amortized,
        "aggregate_saving_pct_at_N": 100.0 * (base - amortized) / base,
        "gpu_baseline_total": N * GPU_BASE,
        "gpu_epra_variable_total": N * (p * GPU_HIT + (1.0 - p) * GPU_FALLBACK),
        "gpu_epra_including_fixed": GPU_FIXED + N * (p * GPU_HIT + (1.0 - p) * GPU_FALLBACK),
    }


def svg_document(title: str, description: str, body: str, width: int = 1080, height: int = 620) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<title>{title}</title><desc>{description}</desc>
<rect width="100%" height="100%" fill="#ffffff"/>
<style>text{{font-family:Arial,sans-serif;fill:#19384a}} .axis{{stroke:#42535c;stroke-width:2}} .grid{{stroke:#dce4e6;stroke-width:1}} .small{{font-size:18px}} .label{{font-size:21px}} .title{{font-size:29px;font-weight:700}}</style>
{body}</svg>'''


def make_break_even_svg(path: Path) -> None:
    left, top, width, height = 100, 105, 900, 410
    xmax, ymax = 3500.0, 650000.0
    sx = lambda x: left + width * x / xmax
    sy = lambda y: top + height * (1 - y / ymax)
    parts = [f'<text x="75" y="52" class="title">Modeled cost and strict break-even</text>']
    for v in range(0, 651, 50):
        yv = v * 1000
        parts.append(f'<line class="grid" x1="{left}" y1="{sy(yv):.1f}" x2="{left+width}" y2="{sy(yv):.1f}"/>')
        parts.append(f'<text x="{left-15}" y="{sy(yv)+6:.1f}" text-anchor="end" class="small">{v}</text>')
    for v in range(0, 3501, 500):
        parts.append(f'<line class="grid" x1="{sx(v):.1f}" y1="{top}" x2="{sx(v):.1f}" y2="{top+height}"/>')
        parts.append(f'<text x="{sx(v):.1f}" y="{top+height+31}" text-anchor="middle" class="small">{v}</text>')
    ybase = lambda n: n * B
    yra = lambda n: K + n * (P0 * H + (1 - P0) * M)
    parts.append(f'<line class="axis" x1="{left}" y1="{top+height}" x2="{left+width}" y2="{top+height}"/>')
    parts.append(f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top+height}"/>')
    parts.append(f'<line x1="{sx(0):.1f}" y1="{sy(ybase(0)):.1f}" x2="{sx(xmax):.1f}" y2="{sy(ybase(xmax)):.1f}" stroke="#19384a" stroke-width="5"/>')
    parts.append(f'<line x1="{sx(0):.1f}" y1="{sy(yra(0)):.1f}" x2="{sx(xmax):.1f}" y2="{sy(yra(xmax)):.1f}" stroke="#087d7d" stroke-width="5"/>')
    cross = K / (B - (P0 * H + (1 - P0) * M))
    parts.append(f'<line x1="{sx(cross):.1f}" y1="{top}" x2="{sx(cross):.1f}" y2="{top+height}" stroke="#c16e2d" stroke-width="2" stroke-dasharray="8 8"/>')
    parts.append(f'<circle cx="{sx(cross):.1f}" cy="{sy(ybase(cross)):.1f}" r="7" fill="#c16e2d"/>')
    parts.append(f'<text x="{sx(cross)+12:.1f}" y="{sy(ybase(cross))-12:.1f}" class="small">break-even: {math.floor(cross)+1} requests</text>')
    parts.append(f'<text x="{left+width/2}" y="590" text-anchor="middle" class="label">Requests over the observation horizon</text>')
    parts.append(f'<text transform="translate(28 {top+height/2}) rotate(-90)" text-anchor="middle" class="label">Cumulative modeled cost (thousand units)</text>')
    parts.append('<line x1="700" y1="82" x2="740" y2="82" stroke="#19384a" stroke-width="5"/><text x="750" y="89" class="small">Independent research</text>')
    parts.append('<line x1="700" y1="111" x2="740" y2="111" stroke="#087d7d" stroke-width="5"/><text x="750" y="118" class="small">EPRA at 70% eligible reuse</text>')
    parts.append('<text x="75" y="605" class="small">Illustrative parameters only; no measured compute or energy results.</text>')
    path.write_text(svg_document("Modeled cost and strict break-even", "Illustrative cumulative cost for independent research and amortized evidence packets.", "".join(parts)), encoding="utf-8")


def make_savings_svg(path: Path) -> None:
    left, top, width, height = 100, 105, 900, 410
    sx = lambda p: left + width * p
    sy = lambda v: top + height * (1 - (v + 20) / 90)
    parts = [f'<text x="75" y="52" class="title">Modeled savings versus eligible reuse</text>']
    for v in range(-20, 71, 10):
        parts.append(f'<line class="grid" x1="{left}" y1="{sy(v):.1f}" x2="{left+width}" y2="{sy(v):.1f}"/>')
        parts.append(f'<text x="{left-14}" y="{sy(v)+6:.1f}" text-anchor="end" class="small">{v}%</text>')
    for v in range(0, 101, 10):
        parts.append(f'<line class="grid" x1="{sx(v/100):.1f}" y1="{top}" x2="{sx(v/100):.1f}" y2="{top+height}"/>')
        parts.append(f'<text x="{sx(v/100):.1f}" y="{top+height+31}" text-anchor="middle" class="small">{v}</text>')
    parts.append(f'<line class="axis" x1="{left}" y1="{sy(0):.1f}" x2="{left+width}" y2="{sy(0):.1f}"/>')
    parts.append(f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top+height}"/>')
    coords = []
    for step in range(101):
        p = step / 100
        saving = estimate(p)["aggregate_saving_pct_at_N"]
        coords.append(f'{sx(p):.1f},{sy(float(saving)):.1f}')
    point_list = " ".join(coords)
    parts.append(f'<polyline points="{point_list}" fill="none" stroke="#087d7d" stroke-width="5"/>')
    for p in (0.3, 0.5, 0.7, 0.9):
        saving = float(estimate(p)["aggregate_saving_pct_at_N"])
        parts.append(f'<circle cx="{sx(p):.1f}" cy="{sy(saving):.1f}" r="7" fill="#c16e2d"/>')
        parts.append(f'<text x="{sx(p)+10:.1f}" y="{sy(saving)-12:.1f}" class="small">{saving:.1f}%</text>')
    parts.append(f'<text x="{left+width/2}" y="590" text-anchor="middle" class="label">Effective eligible packet reuse rate</text>')
    parts.append(f'<text transform="translate(28 {top+height/2}) rotate(-90)" text-anchor="middle" class="label">Modeled aggregate cost reduction</text>')
    parts.append('<text x="75" y="605" class="small">N = 2,000; fixed setup/maintenance = 44,000 illustrative units.</text>')
    path.write_text(svg_document("Modeled savings versus eligible reuse", "Illustrative cost reduction at a fixed workload and overhead.", "".join(parts)), encoding="utf-8")


def make_gpu_svg(path: Path) -> None:
    vals = [
        ("Independent baseline", GPU_BASE, "#19384a"),
        ("EPRA variable", P0 * GPU_HIT + (1 - P0) * GPU_FALLBACK, "#087d7d"),
        ("EPRA incl. fixed / N", (GPU_FIXED + N * (P0 * GPU_HIT + (1 - P0) * GPU_FALLBACK)) / N, "#c16e2d"),
    ]
    left, top, width = 300, 145, 680
    parts = [f'<text x="75" y="52" class="title">Illustrative accelerator accounting</text>',
             f'<line class="axis" x1="{left}" y1="120" x2="{left}" y2="470"/>']
    for v in range(0, 141, 20):
        x = left + width * v / 140
        parts.append(f'<line class="grid" x1="{x:.1f}" y1="120" x2="{x:.1f}" y2="470"/>')
        parts.append(f'<text x="{x:.1f}" y="500" text-anchor="middle" class="small">{v}</text>')
    for i, (label, value, color) in enumerate(vals):
        y = top + i * 105
        parts.append(f'<text x="280" y="{y+29}" text-anchor="end" class="small">{label}</text>')
        parts.append(f'<rect x="{left}" y="{y}" width="{width*value/140:.1f}" height="48" fill="{color}"/>')
        parts.append(f'<text x="{left+width*value/140+12:.1f}" y="{y+32}" class="label">{value:.1f}</text>')
    parts.append('<text x="640" y="555" text-anchor="middle" class="label">Hypothetical accelerator cost units per request</text>')
    parts.append('<text x="75" y="605" class="small">Not GPU-joules, GPU-hours, telemetry, or measured financial cost.</text>')
    path.write_text(svg_document("Illustrative accelerator accounting", "Synthetic arithmetic with a separate fixed GPU overhead.", "".join(parts)), encoding="utf-8")


def write_model_outputs(root: Path) -> None:
    (root / "figures").mkdir(parents=True, exist_ok=True)
    (root / "data").mkdir(parents=True, exist_ok=True)
    rows = [estimate(p) for p in (0.30, 0.50, 0.70, 0.90)]
    with (root / "data" / "sensitivity.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    make_break_even_svg(root / "figures" / "break_even.svg")
    make_savings_svg(root / "figures" / "savings_by_reuse.svg")
    make_gpu_svg(root / "figures" / "gpu_components.svg")
    base = N * B
    q0 = P0 * H + (1.0 - P0) * M
    epra = K + N * q0
    delta = B - q0
    print(f"baseline cost at N={N}: {base:,.0f}")
    print(f"EPRA modeled cost at N={N}, p={P0:.2f}: {epra:,.0f}")
    print(f"modeled saving: {(base-epra)/base*100:.2f}%")
    print(f"strict break-even: {math.floor(K/delta)+1} requests")
    print("All inputs and outputs are illustrative, not measured results.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path.cwd())
    args = parser.parse_args()
    write_model_outputs(args.output_dir.resolve())


if __name__ == "__main__":
    main()
