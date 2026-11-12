# SCÉNA PTÁK — racek ze stock videa (Mixkit 45246, volná licence) vyříznutý z oblohy, reaguje na hudbu.
# Vnitřní režisér střídá looky (klid = spíš reál, plná hudba a dropy = abstrakce):
#   reál       fotka, máchnutí na beat, rozpad na částice
#   chrono     chronofotografie (Marey): až 6 kopií ptáka z různých okamžiků, rozestup podle tempa
#   slit       slit-scan: každý pixel z jiného okamžiku (Time Machine TOP), hloubka času podle hutnosti
#   ink        obrys ptáka se rozpíjí do kouře proudícího šumovým polem
#   kaleido    pták zrcadlený do symetrického tvora, zrcadla se točí s energií
# Základní reakce:
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
		burst=0.0, lastBurst=-9.0, beats=0, look='real', lookBeat=0, lookT=0.0, avgB=0.0, lastDrop=-99.0, hue=random.random(),
		pat=0.0, patT=0.0, jolt=0.0, mir=0.0, W=dict(LOOKS['real'])))

LOOKS = {                                                  # váhy vrstev pro každý look
	'real':    dict(real=1.0, slit=0.0, chrono=0.0, ink=0.0, fold=0.0, sat=0.0),
	'chrono':  dict(real=.2, slit=0.0, chrono=1.0, ink=0.0, fold=0.0, sat=.55),
	'slit':    dict(real=.0, slit=1.0, chrono=0.0, ink=.25, fold=0.0, sat=.75),
	'ink':     dict(real=.3, slit=0.0, chrono=0.0, ink=1.0, fold=0.0, sat=.8),
	'kaleido': dict(real=.5, slit=.6, chrono=0.0, ink=.3, fold=1.0, sat=.65),
}
CALM, WILD = ['real', 'chrono'], ['slit', 'ink', 'kaleido']

def direct(A, dt, now, on, B):
	"""vybere look: ručně, nebo podle hudby (fráze po 8 taktech, drop → abstrakce, klid → reál)"""
	man = P('Blook')
	if man != 'auto':
		S['look'] = man; return
	S['avgB'] += (B - S['avgB']) * min(1.0, dt / 8)
	S['lookT'] += dt
	ab = P('Babstract')
	def pick(wild):
		pool = [l for l in (WILD if wild else CALM) if l != S['look']] or (WILD if wild else CALM)
		S['look'] = random.choice(pool); S['lookBeat'] = S['beats']; S['lookT'] = 0.0
	if on:
		if B - S['avgB'] > .2 and B > .55 and now - S['lastDrop'] > 15:        # drop → hned abstraktní look
			S['lastDrop'] = now; pick(random.random() < .4 + ab * .6)
		elif S['beats'] - S['lookBeat'] >= 32 or (S['lookT'] > 25 and S['beats'] - S['lookBeat'] < 2):
			pick(random.random() < ab * (.25 + B * .75))
		elif B < .2 and S['look'] in WILD and S['lookT'] > 4:             # ztichne → zpátky k reálu
			pick(False)
	elif S['lookT'] > 12:
		pick(random.random() < ab * .5)

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
	# ── režie looků a jejich reakce na hudbu ──
	direct(A, dt, now, on, B)
	tgt = LOOKS[S['look']]; W = S['W']; kf = 1 - math.exp(-dt * 1.4)
	for key_, val in tgt.items(): W[key_] += (val - W[key_]) * kf
	S['hue'] += dt * (.02 + (A['centroid'] * .05 + B * .04) * on)
	tempo = A['tempo'] if (on and A['bpm']) else 1
	# houpání pro časové looky: pták krouží v rytmu, takže kopie v čase se rozestoupí a slit-scan má co natahovat
	S['sway'] = S.get('sway', 0.0) + dt * (.8 + tempo * 1.2) * (1 + A['kickEnv'] * on)
	amp = (W['chrono'] * .26 + W['slit'] * .22) * (1 + B * .6)
	sw = k('sway').par
	sw.tx = math.sin(S['sway']) * amp; sw.ty = math.sin(S['sway'] * .63 + 1.3) * amp * .55
	sw.rotate = math.sin(S['sway'] * .41) * amp * 60
	ce = k('center').par
	ce.tx, ce.ty = .5 - S['cx'], .5 - S['cy']; ce.sx = ce.sy = 1.15 + B * .25
	# chronofoto: rozestup kopií = půl doby (podle tempa), počet podle hutnosti, nejnovější kopie blikne na kopák
	step = max(3, min(14, int(round((60.0 / A['bpm'] if (on and A['bpm']) else .5) * 30 / 2))))
	for i in range(1, 6):
		e_ = k('echo%d' % i).par; e_.blackoffset = e_.whiteoffset = min(58, i * step)
	setv(k('chrono'), 0, (3 + round(B * 3) if on else 4, .86, .07 + A['centroid'] * .08, W['sat']))
	setv(k('chrono'), 1, (S['hue'], A['kickEnv'] * .6 * on, 0, 0))
	# slit-scan: hloubka času podle hutnosti, virbl ji trhne, vzor se mění po 16 dobách
	if A['snareHit']: S['jolt'] = max(S['jolt'], A['snareHit'] * 15 * R)
	S['jolt'] *= math.exp(-dt * 3)
	if A['kickHit'] and S['beats'] % 16 == 0: S['patT'] = random.choice((0., 1., 2., 3.))
	S['pat'] += (S['patT'] - S['pat']) * (1 - math.exp(-dt * .8))
	k('slit').par.whiteoffset = min(58, 8 + (B * 40 + S['jolt']) * on + (0 if on else 20))
	setv(k('tmap'), 0, (S['pat'], S['t'], S['cx'], S['cy']))
	setv(k('tmap'), 1, (S['ux'], S['uy'], asp, 0))
	# inkoust: rychlost proudění podle energie, kopák vpustí víc inkoustu
	setv(k('ink'), 0, (S['t'], 1 + (A['energy'] * 3 + B * 2) * on, min(.985, .9 + P('Btrails') * .07), 1 + A['kickEnv'] * 2 * on))
	setv(k('ink'), 1, (S['hue'] + .5, W['sat'], asp, 1.6 + b['air'] * 2 * on))
	# mix looků + kaleidoskop (zrcadla se točí s energií jako u Krasohledu)
	setv(k('look'), 0, (W['real'], W['slit'], W['chrono'], W['ink']))
	setv(k('look'), 1, (S['hue'], W['sat'], 1.0, 0))
	S['mir'] = (S['mir'] + dt * (8 + (A['energy'] * 40 + B * 30) * R * on) * tempo) % 360.0
	setv(k('fold'), 0, (S['mir'] * .5, 90 + S['mir'], 45 - S['mir'] * .3, 180))
	setv(k('fold'), 1, (90, 4, asp, 0))
	k('fold_mix').par.cross = W['fold']
	# ── světelné stopy: delší při plné hudbě, unáší je dozadu proti směru letu ──
	k('fb_lvl').par.opacity = min(.93, P('Btrails') * (.55 + B * .35 + A['kickEnv'] * .1))
	fx = k('fb_xf').par
	fx.sx = fx.sy = .996 - A['kickEnv'] * .01 * on
	fx.tx = -S['uy'] * .002; fx.ty = S['ux'] * .002
