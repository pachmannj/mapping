# SCÉNA PTÁK — racek ze stock videa (Mixkit 45246, volná licence) vyříznutý z oblohy, reaguje na hudbu:
#   kopák   → máchnutí křídly (deformace obrazu kolem ramen), rychlost mávání podle tempa
#   silný úder / drop → rozpad na částice, které se pružinou složí zpět
#   hutnost a výšky → délka světelných stop a chvění částic; video plyne pomalu, konec smyčky se prolne se začátkem
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
	S.update(dict(vt=0.0, cx=.5, cy=.5, ux=1.0, uy=0.0, span=.3, phase=1.0, flapRate=1.5, idle=1.5, dis=0.0, t=0.0,
		burst=0.0, lastBurst=-9.0, beats=0))

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
	rend = k('render'); asp = rend.width / max(1, rend.height)
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
	# ── rozpad na částice: silný úder, nebo každý 8. úder při plné hudbě ──
	burst = 0.0
	strong = A['kickHit'] > .75 or (A['kickHit'] and B > .6 and S['beats'] % 8 == 0)
	if on and strong and now - S['lastBurst'] > 1.2:
		burst = (1.2 + A['kickHit'] * 1.6) * P('Bdissolve') * R; S['lastBurst'] = now; S['dis'] = 1.0
	if not on and now - S['lastBurst'] > 6:
		burst = 1.0 * P('Bdissolve'); S['lastBurst'] = now; S['dis'] = 1.0
	S['dis'] *= math.exp(-dt * 1.1)
	wx, wy = (S['cx'] - .5) * 2 * asp, (S['cy'] - .5) * 2
	setv(k('parts'), 0, (S['t'], dt, burst, 3.5 + B * 2))
	setv(k('parts'), 1, (wx, wy, (A['hatEnv'] * .8 + b['air'] * .3) * R * on, asp))
	setv(k('parts'), 2, (min(1.0, S['dis'] * 1.6 + .05), P('Bbright'), 0, 0))
	setv(k('key'), 0, (.05, .15, P('Bbright'), 0))
	k('photo_lvl').par.brightness1 = max(0.0, 1.0 - S['dis'] * 1.4)        # fotka ustoupí, když se pták rozpadne
	setv(k('mat'), 0, (P('Bsize'), rend.width, rend.height, 0))
	# ── světelné stopy: delší při plné hudbě, unáší je dozadu proti směru letu ──
	k('fb_lvl').par.opacity = min(.93, P('Btrails') * (.55 + B * .35 + A['kickEnv'] * .1))
	fx = k('fb_xf').par
	fx.sx = fx.sy = .996 - A['kickEnv'] * .01 * on
	fx.tx = -S['uy'] * .002; fx.ty = S['ux'] * .002
