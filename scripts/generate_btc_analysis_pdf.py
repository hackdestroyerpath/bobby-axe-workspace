#!/usr/bin/env python3
import json
import math
import os
from textwrap import wrap

INPUT = "/home/openclaw/.openclaw/workspace-bobbys/storage/curated/analysis_results/BTCUSDC/analysis__BTCUSDC__2026-03-22T01-28-23Z__corr-4fecd06e-dfa5-4d9b-918f-90a4fec0c56b.json"
OUTPUT = "/home/openclaw/.openclaw/workspace-jusetta/reports/BTCUSDC_snapshot-4fecd06e-dfa5-4d9b-918f-90a4fec0c56b_analysis.pdf"


def pdf_escape(text: str) -> str:
    return text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')


def cp1251_bytes(text: str) -> bytes:
    return text.encode('cp1251', errors='replace')


def text_line(text: str, x: int, y: int, size: int = 12, font: str = 'F1') -> bytes:
    escaped = pdf_escape(text)
    return f"BT /{font} {size} Tf {x} {y} Td ({escaped}) Tj ET\n".encode('cp1251', errors='replace')


def rect(x, y, w, h, fill_rgb=None, stroke_rgb=None, line_width=1):
    cmds = []
    if line_width != 1:
        cmds.append(f"{line_width} w")
    if fill_rgb is not None:
        cmds.append(f"{fill_rgb[0]:.3f} {fill_rgb[1]:.3f} {fill_rgb[2]:.3f} rg")
    if stroke_rgb is not None:
        cmds.append(f"{stroke_rgb[0]:.3f} {stroke_rgb[1]:.3f} {stroke_rgb[2]:.3f} RG")
    op = 'B' if fill_rgb is not None and stroke_rgb is not None else ('f' if fill_rgb is not None else 'S')
    cmds.append(f"{x} {y} {w} {h} re {op}")
    return ('\n'.join(cmds) + '\n').encode('ascii')


def line(x1, y1, x2, y2, rgb=(0, 0, 0), width=1):
    return f"{width} w {rgb[0]:.3f} {rgb[1]:.3f} {rgb[2]:.3f} RG {x1} {y1} m {x2} {y2} l S\n".encode('ascii')


def build_pdf(data):
    results = data['results']
    summary = data['summary']

    page_w, page_h = 595, 842
    content = bytearray()

    # Background header band
    content += rect(40, 760, 515, 48, fill_rgb=(0.95, 0.67, 0.15), stroke_rgb=None)
    content += text_line('Antares Capital // BTCUSDC analysis snapshot', 56, 790, 20, 'F2')
    content += text_line(f"Snapshot: {data['snapshot_id']}", 56, 772, 10)
    content += text_line(f"As of UTC: {data['as_of_utc']}", 360, 772, 10)

    content += text_line('Executive summary', 50, 735, 16, 'F2')
    content += text_line(f"Overall signal: {summary['overall_signal']}", 50, 715, 12)
    content += text_line(f"Overall confidence: {summary['overall_confidence']:.2f}", 250, 715, 12)
    for i, line_text in enumerate(wrap(summary['final_comment'], width=85)):
        content += text_line(line_text, 50, 697 - i * 14, 11)

    # Chart block
    chart_x, chart_y, chart_w, chart_h = 50, 500, 240, 150
    content += text_line('Strategy confidence chart', chart_x, chart_y + chart_h + 20, 14, 'F2')
    content += rect(chart_x, chart_y, chart_w, chart_h, fill_rgb=(0.98, 0.98, 0.98), stroke_rgb=(0.8, 0.8, 0.8))
    content += line(chart_x + 30, chart_y + 20, chart_x + 30, chart_y + 125, rgb=(0.4, 0.4, 0.4))
    content += line(chart_x + 30, chart_y + 20, chart_x + 210, chart_y + 20, rgb=(0.4, 0.4, 0.4))
    for idx, tick in enumerate([0.25, 0.5, 0.75, 1.0]):
        y = chart_y + 20 + int(105 * tick)
        content += line(chart_x + 28, y, chart_x + 210, y, rgb=(0.88, 0.88, 0.88), width=0.5)
        content += text_line(f"{tick:.2f}", chart_x, y - 3, 8)

    colors = [(0.11, 0.65, 0.85), (0.96, 0.37, 0.47), (0.27, 0.77, 0.45)]
    labels = []
    for r in results:
        avg = sum(frame['confidence'] for frame in r['frames'].values()) / 3
        labels.append((r['strategy'], avg))
    bar_w = 36
    gap = 20
    for i, (label, avg) in enumerate(labels):
        x = chart_x + 48 + i * (bar_w + gap)
        h = int(avg * 105)
        content += rect(x, chart_y + 20, bar_w, h, fill_rgb=colors[i % len(colors)], stroke_rgb=None)
        short = {'trend_following': 'Trend', 'mean_reversion': 'Revert', 'breakout': 'Breakout'}.get(label, label[:8])
        content += text_line(short, x - 2, chart_y + 6, 8)
        content += text_line(f"{avg:.2f}", x + 5, chart_y + 28 + h, 9)

    # Right summary panel
    panel_x = 320
    content += text_line('Per-strategy frame matrix', panel_x, 670, 14, 'F2')
    y = 648
    for r in results:
        content += rect(panel_x, y - 12, 220, 54, fill_rgb=(0.97, 0.97, 1.0), stroke_rgb=(0.85, 0.85, 0.95))
        content += text_line(r['strategy'], panel_x + 10, y + 24, 12, 'F2')
        frames_text = ' | '.join([f"{tf}: {vals['signal']} ({vals['confidence']:.2f})" for tf, vals in r['frames'].items()])
        for j, chunk in enumerate(wrap(frames_text, width=38)):
            content += text_line(chunk, panel_x + 10, y + 8 - j * 12, 9)
        y -= 68

    # Detailed strategy sections
    y = 450
    content += text_line('Detailed strategy notes', 50, y + 20, 16, 'F2')
    y -= 5
    for r in results:
        content += rect(50, y - 56, 495, 64, fill_rgb=(1, 1, 1), stroke_rgb=(0.85, 0.85, 0.85))
        content += text_line(r['strategy'], 60, y - 12, 13, 'F2')
        inner_y = y - 28
        for tf in ['1m', '5m', '60m']:
            vals = r['frames'][tf]
            line_text = f"{tf}: {vals['signal']} / conf {vals['confidence']:.2f} / {vals['conclusion']}"
            wrapped = wrap(line_text, width=88)
            for chunk in wrapped:
                content += text_line(chunk, 60, inner_y, 10)
                inner_y -= 12
        y -= 82

    content += text_line('Design note: current chart is based on strategy-confidence data from Ben_Kim analysis_result.', 50, 66, 9)
    content += text_line('If Jack provides time-series candles, the next PDF version can include full price/volume charts.', 50, 52, 9)

    stream = bytes(content)
    objects = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_w} {page_h}] /Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >>".encode('ascii'))
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
    objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode('ascii') + stream + b"endstream")

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += f"{i} 0 obj\n".encode('ascii') + obj + b"\nendobj\n"
    xref_pos = len(pdf)
    pdf += f"xref\n0 {len(objects)+1}\n".encode('ascii')
    pdf += b"0000000000 65535 f \n"
    for off in offsets[1:]:
        pdf += f"{off:010d} 00000 n \n".encode('ascii')
    pdf += f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode('ascii')
    return pdf


def main():
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(INPUT, 'r', encoding='utf-8') as f:
        data = json.load(f)
    pdf = build_pdf(data)
    with open(OUTPUT, 'wb') as f:
        f.write(pdf)
    print(OUTPUT)


if __name__ == '__main__':
    main()
