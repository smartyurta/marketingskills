#!/usr/bin/env python3
"""Генератор современного QR-кода Smart Yurta с логотипом (SVG + PNG).

Использование:
  pip install segno pillow
  python3 make_qr.py [URL]

По умолчанию кодируется адрес go.html на GitHub Pages. Если файлы лежат на другом
хостинге — передайте полный https-адрес go.html первым аргументом.
"""
import base64, io, sys
from pathlib import Path
import segno
from PIL import Image, ImageDraw

HERE = Path(__file__).parent
URL = sys.argv[1] if len(sys.argv) > 1 else "https://smartyurta.github.io/marketingskills/smart-yurta-qr/go.html"
INK, ACCENT, BG = "#14181f", "#0a5a34", "#ffffff"
QUIET, LOGO_FRAC = 3, 0.20  # поля в модулях; доля стороны под логотип (запас коррекции ошибок H)

qr = segno.make(URL, error=segno.consts.ERROR_LEVELS["H"] if hasattr(segno.consts, "ERROR_LEVELS") else "h", boost_error=False)
matrix = [list(r) for r in qr.matrix]
n = len(matrix)
total = n + 2 * QUIET
c = total / 2
logo_r = n * LOGO_FRAC / 2 + 0.8  # радиус белого круга под логотипом, модулей

def in_eye(x, y):
    return (x < 7 and y < 7) or (x >= n - 7 and y < 7) or (x < 7 and y >= n - 7)

def under_logo(x, y):
    return (x + .5 + QUIET - c) ** 2 + (y + .5 + QUIET - c) ** 2 <= (logo_r + .6) ** 2

# Логотип: чёрное на белом -> маска прозрачности
src = Image.open(HERE / "logo-source.jpg").convert("L")
bbox = Image.eval(src, lambda v: 255 if v < 128 else 0).getbbox()
src = src.crop(bbox)
alpha = src.point(lambda v: 255 - v)
logo = Image.new("RGBA", src.size, INK)
logo.putalpha(alpha)
buf = io.BytesIO(); logo.save(buf, "PNG")
logo_b64 = base64.b64encode(buf.getvalue()).decode()
lw = logo_r * 2 * 0.80
lh = lw * logo.height / logo.width
if lh > logo_r * 2 * 0.80:
    lh = logo_r * 2 * 0.80; lw = lh * logo.width / logo.height

# ---------- SVG ----------
S = []
S.append(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {total} {total}" width="1024" height="1024">')
S.append(f'<title>QR-код — Smart Yurta</title><rect width="{total}" height="{total}" rx="2.2" fill="{BG}"/>')
S.append(f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{INK}"/><stop offset="1" stop-color="#1f3a2e"/></linearGradient></defs>')
dots = []
for y in range(n):
    for x in range(n):
        if matrix[y][x] and not in_eye(x, y) and not under_logo(x, y):
            dots.append(f'<rect x="{x+QUIET+.08:.2f}" y="{y+QUIET+.08:.2f}" width=".84" height=".84" rx=".34"/>')
S.append('<g fill="url(#g)">' + "".join(dots) + '</g>')
for ex, ey in ((0, 0), (n - 7, 0), (0, n - 7)):
    X, Y = ex + QUIET, ey + QUIET
    S.append(f'<rect x="{X+.5}" y="{Y+.5}" width="6" height="6" rx="0.8" fill="none" stroke="{ACCENT}" stroke-width="1"/>')
    S.append(f'<rect x="{X+2}" y="{Y+2}" width="3" height="3" rx="1" fill="{INK}"/>')
S.append(f'<circle cx="{c}" cy="{c}" r="{logo_r}" fill="{BG}"/>')
S.append(f'<circle cx="{c}" cy="{c}" r="{logo_r-.35}" fill="none" stroke="{ACCENT}" stroke-width=".18" opacity=".5"/>')
S.append(f'<image x="{c-lw/2:.2f}" y="{c-lh/2:.2f}" width="{lw:.2f}" height="{lh:.2f}" xlink:href="data:image/png;base64,{logo_b64}"/>')
S.append('</svg>')
(HERE / "qr-smart-yurta.svg").write_text("".join(S), encoding="utf-8")

# ---------- PNG (те же геометрия и цвета, 4x суперсэмплинг) ----------
PX = 1600; K = 4; u = PX * K / total
img = Image.new("RGB", (PX * K, PX * K), BG)
d = ImageDraw.Draw(img)
grad = Image.new("RGB", img.size)
gd = ImageDraw.Draw(grad)
a, b = (0x14, 0x18, 0x1f), (0x1f, 0x3a, 0x2e)
for i in range(0, PX * K, 8):
    t = i / (PX * K)
    gd.rectangle([0, i, PX * K, i + 8], fill=tuple(int(a[j] + (b[j] - a[j]) * t) for j in range(3)))
mask = Image.new("L", img.size, 0); md = ImageDraw.Draw(mask)
for y in range(n):
    for x in range(n):
        if matrix[y][x] and not in_eye(x, y) and not under_logo(x, y):
            X, Y = (x + QUIET) * u, (y + QUIET) * u
            md.rounded_rectangle([X + .08 * u, Y + .08 * u, X + .92 * u, Y + .92 * u], radius=.34 * u, fill=255)
img.paste(grad, (0, 0), mask)
d = ImageDraw.Draw(img)
for ex, ey in ((0, 0), (n - 7, 0), (0, n - 7)):
    X, Y = (ex + QUIET) * u, (ey + QUIET) * u
    d.rounded_rectangle([X, Y, X + 7 * u, Y + 7 * u], radius=1.3 * u, fill=ACCENT)
    d.rounded_rectangle([X + u, Y + u, X + 6 * u, Y + 6 * u], radius=.6 * u, fill=BG)
    d.rounded_rectangle([X + 2 * u, Y + 2 * u, X + 5 * u, Y + 5 * u], radius=1 * u, fill=INK)
d.ellipse([(c - logo_r) * u, (c - logo_r) * u, (c + logo_r) * u, (c + logo_r) * u], fill=BG)
lg = logo.resize((int(lw * u), int(lh * u)), Image.LANCZOS)
img.paste(lg, (int((c - lw / 2) * u), int((c - lh / 2) * u)), lg)
img = img.resize((PX, PX), Image.LANCZOS)
img.save(HERE / "qr-smart-yurta.png")
print("OK:", URL, f"({n}x{n} модулей)")
