# Vyrobí atlas znaků pro scénu Kytice (media/glyphs.png): 16 sloupců × 2 řádky, buňka 32 × 48 px, bílé na černé.
# Řádek 0 = ASCII znaky, řádek 1 = písmena; v obou seřazené od nejřidšího po nejhustší (podle množství „inkoustu“),
# takže shader jen podle jasu vybere sloupec. Spuštění: python3 tools/make_glyphs.py (potřebuje Pillow a písmo Menlo z macOS).
from PIL import Image, ImageDraw, ImageFont
import os

W, H, N = 32, 48, 16
font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 40)
ROWS = [" .'`,:;-~_=+*^\"!/|\\()<>?ixzcvo%#&@$8B0QWM",
        " ilrtjfcvszxyaeounkhdbqpgwmKVETINAFLHRSGBDOQWM"]

def ink(ch):
	im = Image.new('L', (W, H)); d = ImageDraw.Draw(im)
	d.text((W / 2, H / 2), ch, font=font, fill=255, anchor='mm')
	return sum(im.getdata()) / (W * H * 255.0), im

atlas = Image.new('L', (W * N, H * len(ROWS)))
for r, cands in enumerate(ROWS):
	scored = sorted({c: ink(c) for c in cands}.items(), key=lambda kv: kv[1][0])
	pick = [scored[round(i * (len(scored) - 1) / (N - 1))] for i in range(N)]
	print('řádek %d:' % r, ''.join(c for c, _ in pick))
	for i, (c, (_, im)) in enumerate(pick):
		atlas.paste(im, (i * W, r * H))
out = os.path.join(os.path.dirname(__file__), '..', 'media', 'glyphs.png')
atlas.convert('RGB').save(out); print('uloženo', os.path.normpath(out))
