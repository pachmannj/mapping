# SCÉNA PTÁK — racek ze stock videa (Mixkit 45246, volná licence) vyříznutý z oblohy, ve 3D okně ve zdi
# (anamorfní iluze jako billboardy v New Yorku): krouží ve výklenku a s hudbou z něj vylétá před zeď.
# Styl ze čtyř vrstev: šedé tělo s bílým obrysem, tyrkysové světelné stopy, červeno-oranžový barevný lem, rastr z teček.
#   kopák   → máchnutí křídly + bílý záblesk obrysu, postrčí ptáka dopředu z okna
#   energie / hutnost → jak daleko z okna vylétá, délka stop
#   virbl a hi-haty → rastr z teček (halftone) a barevný lem
import math, random
import numpy as np

SHOW = '/project1/show'
Bd = '/project1/show/bird'
S = {}

def P(name): return getattr(op(SHOW).par, name).eval()
def k(name): return op(Bd + '/' + name)

def num(x):
	# TD 2025.33230 převádí subnormální čísla (např. doznívající záblesk 5e-324) na 1.8e308 → bílý obraz; NaN/inf taky pryč
	x = float(x)
	return 0.0 if x != x or abs(x) < 1e-12 or abs(x) > 1e12 else x

def setv(o, i, v):
	p = o.par
	getattr(p, 'vec%dvaluex' % i).val, getattr(p, 'vec%dvaluey' % i).val = num(v[0]), num(v[1])
	getattr(p, 'vec%dvaluez' % i).val, getattr(p, 'vec%dvaluew' % i).val = num(v[2]), num(v[3])

def reset():
	S.clear()
	S.update(dict(vt=0.0, cx=.5, cy=.5, ux=1.0, uy=0.0, span=.3, phase=1.0, flapRate=1.5, idle=1.5, t=0.0, beats=0,
		z=-.6, zv=0.0, path=0.0, px=0.0, py=0.0, half=0.0, fr=0.0, hue=0.0))

def window(w, A, on, obj, edgePulse, hue, wall=1.0, wallY=0.0):
	"""společné nastavení 3D okna (stejné jako v sc_flower.py); obj = (x, y, z, poloviční výška karty, poměr stran)"""
	asp = w.width / max(1, w.height)
	H = P('Wsize'); W = min(asp * .92, H * 1.5); oy = -.08
	setv(w, 0, (0, P('Weye'), P('Wdist') * 2, asp))
	setv(w, 1, (W, H, P('Wdepth'), P('Wedges') * (.35 + A['energy'] * .4 * on)))
	setv(w, 2, obj[:4])
	setv(w, 3, (obj[4], .4, oy + H + .7, 1.6))
	setv(w, 4, (hue, P('Wgrid'), P('Wrefl'), P('Wshadow')))
	setv(w, 5, (edgePulse, P('Wlight'), 1.0, oy))
	setv(w, 6, (1 if P('Wbox') else 0, P('Wwall') * wall, 1.15, wallY))
	return H, oy

def track(asp):
	"""střed těla a osa rozpětí z masky (64×36 px, levné čtení z GPU)"""
	a = k('mask_small').numpyArray()
	if a is None or a.size == 0: return
	m = a[:, :, 3].astype(np.float64)
	tot = m.sum()
	if tot < 1.0: return
	h, w = m.shape
	ys, xs = np.mgrid[0:h, 0:w]
	u = (xs + .5) / w; v = (ys + .5) / h
	cx = float((m * u).sum() / tot); cy = float((m * v).sum() / tot)
	dx = (u - cx) * asp; dy = v - cy
	cxx = float((m * dx * dx).sum() / tot); cyy = float((m * dy * dy).sum() / tot); cxy = float((m * dx * dy).sum() / tot)
	ang = .5 * math.atan2(2 * cxy, cxx - cyy)              # hlavní osa = rozpětí křídel
	ux, uy = math.cos(ang), math.sin(ang)
	if ux * S['ux'] + uy * S['uy'] < 0: ux, uy = -ux, -uy  # bez přeskakování směru o 180°
	span = 2.0 * math.sqrt(max(cxx * ux * ux + 2 * cxy * ux * uy + cyy * uy * uy, 1e-6)) * 1.6
	f = .15
	S['cx'] += (cx - S['cx']) * f; S['cy'] += (cy - S['cy']) * f
	S['ux'] += (ux - S['ux']) * f; S['uy'] += (uy - S['uy']) * f
	S['span'] += (span - S['span']) * f

def update(A, dt, now):
	if not S: reset()
	on = A['on']; R = P('Reactivity'); b = A['bands']; B = A['busy'] if on else 0
	S['t'] += dt
	asp = 16 / 9
	# ── video plyne plynule (přeskakování na čas by každý snímek dekódovalo H.264 od klíčového snímku → 20 fps), s energií rychleji ──
	k('video').par.speed = P('Bspeed') * (.35 + (A['energy'] * .4 + B * .3) * on)
	track(asp)
	# ── máchnutí: každý kopák spustí jeden mávnutí; rychlost podle tempa ──
	if A['kickHit'] and on:
		S['phase'] = 0.0; S['beats'] += 1
		S['flapRate'] = max(1.2, min(3.5, (A['bpm'] / 60.0) * 1.1)) if A['bpm'] else 2.0
	elif not on:
		S['idle'] -= dt
		if S['idle'] <= 0: S['phase'] = 0.0; S['flapRate'] = 1.2; S['idle'] = random.uniform(1.8, 3.2)
	S['phase'] = min(1.0, S['phase'] + dt * S['flapRate'])
	ph = S['phase']
	amp = P('Bflap') * (.45 + (A['kickEnv'] * .35 + b['low'] * .2) * R * on) if on else .4 * P('Bflap')
	glide = math.sin(S['t'] * .7) * .05                    # klidné plachtění mezi mávnutími
	flap = (math.cos(ph * 2 * math.pi) * amp if ph < 1.0 else 0.0) * (1 - ph * .3) + glide
	setv(k('flap'), 0, (S['cx'], S['cy'], S['ux'], S['uy']))
	setv(k('flap'), 1, (flap, S['span'] * .16, S['span'], asp))
	setv(k('key'), 0, (.05, .15, 1.0, 0))
	ce = k('center').par
	ce.tx, ce.ty = .5 - S['cx'], .5 - S['cy']
	# ── let v prostoru: krouží ve výklenku (osmička), s energií vylétá z okna, kopák ho postrčí dopředu ──
	tempo = A['tempo'] if (on and A['bpm']) else 1
	S['path'] += dt * (.25 + (A['energy'] * .3 + B * .3) * on) * tempo
	D = P('Wdepth'); pop = P('Wpop'); H = P('Wsize')
	zt = -D * .55 + (A['energy'] * .7 + B * .7 + .15 * on) * pop * (D * .55 + .8)
	S['zv'] += ((zt - S['z']) * 4.0 - S['zv'] * 3.5) * dt + A['kickHit'] * .4 * R * pop * on
	S['z'] += S['zv'] * dt
	tx = math.sin(S['path']) * H * .55; ty = math.sin(S['path'] * 2) * H * .22 - .05
	vx = (tx - S['px']) / max(dt, 1e-3); vy = (ty - S['py']) / max(dt, 1e-3)
	S['px'], S['py'] = tx, ty
	hh = .9 * P('Bsize') * H
	# ── styl: stopy za pohybem (proti směru letu), lem a rastr podle virblu a hi-hatů ──
	if A['snareHit'] and on: S['half'] = max(S['half'], .6 + A['snareHit'] * .6)
	S['half'] *= math.exp(-dt * 2.5)
	S['fr'] += ((.4 + A['hatEnv'] * 1.2 + b['air'] * .5) * on - S['fr']) * (1 - math.exp(-dt * 8))
	S['hue'] += dt * (.005 + A['centroid'] * .02 * on)
	tr = P('Btrails')
	dx, dy = -vx * 60 - 1.5, -vy * 60 - .8                  # px za snímek ve 960×540
	sp = math.hypot(dx, dy); mx = 4 + B * 4
	if sp > mx: dx, dy = dx / sp * mx, dy / sp * mx
	setv(k('reel'), 0, (dx, dy, min(.97, .8 + tr * .15 + B * .03), tr * (1.0 + A['kickEnv'] * .8 * on)))
	setv(k('reel'), 1, (5 + 6 * S['fr'], P('Bfringe') * (.5 + S['fr']), min(1.0, P('Bhalftone') * (S['half'] + B * .35 * on)), 6))
	setv(k('reel'), 2, (P('Bbright') * .8, P('Bbright'), math.sin(S['hue'] * 6.28) * .06, A['kickEnv'] * .8 * on))
	window(k('window'), A, on, (tx, ty, S['z'], hh, asp), A['kickEnv'] * on, .5 + S['hue'])

def look_name(): return 'okno'
