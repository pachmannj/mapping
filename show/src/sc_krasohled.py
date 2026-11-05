# SCÉNA KRASOHLED — síť přehozená přes ikonu, laloky podle 12 pásem, GPU částice, stopy, krasohledový post.
# Port z Portfolio/2.0/touchdesigner/krasohled_engine.py; zvuk bere ze sdílené analýzy (engine.A).
import math, random, time, colorsys

SHOW = '/project1/show'
K = '/project1/show/krasohled'
S = {}
NAMES = dict(Speed='Kspeed', Scene='Kscene', Strobe='Kstrobe', Camera='Camtrails')
SEQ = [4, 6, 3, 8, 5, 4, 7, 12, 6, 4]

def P(name):
	if name == 'Reactivity': return op(SHOW).par.Reactivity.eval() * 2
	return getattr(op(SHOW).par, NAMES.get(name, name)).eval()

def k(name): return op(K + '/' + name)

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
	S.update(dict(t=0.0, rot=0.0, rotV=0.0, twist=0.0, hue=random.random(), colorMix=0.0, scaleS=0.0, shockR=9.0, shockA=0.0,
		lobeKick=0.0, ringKick=0.0, seedA=random.random() * 10, seedB=random.random() * 10,
		n1=7.0, n2=7.0, mixT=1.0, seqI=0, nextAt=0.0, flash=0.0, clock=0.0, beats=0))
	S['seedAT'] = S['seedA']; S['seedBT'] = S['seedB']

def morph(n):
	S['n1'] = S['n1'] if S['mixT'] < .5 else S['n2']
	S['n2'] = float(n); S['mixT'] = 0.0

def on_kick(A, kk):
	r = P('Reactivity'); B = A['busy']
	S['beats'] += 1
	S['shockR'] = 0.0; S['shockA'] = max(S['shockA'], (.012 + .05 * B) * r * (.5 + kk))
	S['lobeKick'] = min(.8, S['lobeKick'] + kk * .35)
	S['hue'] += (.02 + kk * .04) * (.5 + B)
	if P('Lobes') == 0 and S['beats'] % 8 == 0:
		S['seqI'] = (S['seqI'] + 1) % len(SEQ); morph(SEQ[S['seqI']])
	if S['beats'] % 32 == 0:
		S['seedAT'] = random.random() * 10; S['seedBT'] = random.random() * 10; S['ringKick'] = (random.random() - .5) * .1

def update(A, dt, now):
	if not S: reset()
	if A['kickHit']: on_kick(A, A['kickHit'])
	if A['snareHit']:
		S['rotV'] += (1 if random.random() < .5 else -1) * A['snareHit'] * (.04 + .3 * A['busy']) * P('Reactivity')
	sp, r = P('Speed'), P('Reactivity'); on = 1 if A['on'] else 0
	B = on * A['busy']; I = (.35 + B * 1.65) * r / 2
	tempo = A['tempo'] if (on and A['bpm']) else 1
	b = A['bands']
	S['t'] += dt * sp * ((.45 + tempo * .75 + B * .5) if on else .85)
	S['rotV'] *= math.exp(-dt * 1.2)
	S['rot'] += dt * sp * (.04 * (tempo if on else 1) + on * (b['air'] * .08 + A['hatEnv'] * .1) * I) + S['rotV'] * dt
	S['twist'] += (((A['centroid'] - .35) * (.4 + B * 1.4) * r if on else math.sin(S['t'] * .13) * .15) - S['twist']) * .03
	S['scaleS'] += ((B * .11 * r / 2 if on else 0) - S['scaleS']) * (1 - math.exp(-dt * 1.2))
	S['seedA'] += (S['seedAT'] - S['seedA']) * dt * .3; S['seedB'] += (S['seedBT'] - S['seedB']) * dt * .3
	S['shockR'] += dt * .9; S['shockA'] *= math.exp(-dt * 1.4)
	S['lobeKick'] *= math.exp(-dt * 2.5); S['ringKick'] *= math.exp(-dt * .15)
	S['hue'] += dt * (.03 + on * (.05 + A['centroid'] * .06 + B * .15) * r)
	S['colorMix'] += ((1 if P('Colour') else 0) - S['colorMix']) * .03
	lobes = int(P('Lobes'))
	if lobes == 0 and not on and now > S['nextAt']:
		S['seqI'] = (S['seqI'] + 1) % len(SEQ); morph(SEQ[S['seqI']]); S['nextAt'] = now + 7 / max(.3, sp)
	if lobes > 0 and S['n2'] != lobes: morph(lobes)
	S['mixT'] = min(1.0, S['mixT'] + dt * .45 * max(.3, sp))
	m = S['mixT']; e = 4 * m ** 3 if m < .5 else 1 - (-2 * m + 2) ** 3 / 2
	nn = max(S['n1'], S['n2']); t = S['t']
	lobeR = (.26 + .06 * math.sin(t * .37 + S['seedA'])) * min(1, 4.6 / nn + .1) * (1 + b['low'] * .06 * r + S['lobeKick'] * .06)
	ring = .44 + .06 * math.sin(t * .29 + S['seedB']) + S['ringKick'] + A['energy'] * .015 * r * math.sin(t * .5)
	rend = k('render1'); asp = rend.width / max(1, rend.height)
	scale = .86 * min(1, asp) / 1.08
	dens = P('Density'); g = min(1, 200 / dens); moire = P('Moire')
	U = dict(
		uA=(t, S['n1'], S['n2'], e),
		uB=(S['rot'], lobeR, ring, .2 + .05 * math.sin(t * .5)),
		uC=(1 + min(1.3, (b['sub'] * .25 + A['kickEnv'] * .3 + S['lobeKick'] * .15) * I),
			P('Ripple') * (1 + (b['mid'] * .5 + A['snareEnv'] * .4 + A['sustain'] * .4) * I * 2), P('Relief'), asp),
		uD=((b['air'] * .4 + A['hatEnv'] * .3) * r, 0.0, scale, S['twist']),
		uE=(.92 + A['centroid'] * .18 + B * .25, S['shockR'], S['shockA'], (b['air'] * .05 + A['hatEnv'] * .1) * I * 2 * B),
		uF=(S['scaleS'] + A['kickEnv'] * .02 * I, A['kickEnv'] * .25 * I, S['hue'], S['colorMix']),
		uG=((.5 + B * 1.1) * r / 2 if on else 0, A['energy'] * (.3 + B * .6) * r / 2 if on else 0, ((.55 if moire else .8) * g + .1), 0),
		uL0=tuple(A['LOB'][0:4]), uL1=tuple(A['LOB'][4:8]), uL2=tuple(A['LOB'][8:12]))
	for name in ('a', 'b'):
		mat = k('mat_' + name)
		for i, (key, val) in enumerate(U.items()):
			if key == 'uG' and name == 'b': val = (val[0], val[1], .45 * g + .08, 0)
			if key == 'uD' and name == 'b': val = (val[0], .045 + math.sin(t * .11) * .02 + A['hatEnv'] * .004 * r, val[2], val[3])
			setv(mat, i, val)
	k('geo_b').render = bool(moire)
	live(A, dt, lobeR, ring, asp, scale, B, tempo, on)

# ─── vrstvy navíc: částice, zpětná vazba, post a vnitřní scény (režisér) ───
SCENES = {
	'clean':  dict(fb=0.0, trail=0.0, zoom=1.0, rot=0.0, kal=0.0, seg=6, bloom=.3, ca=0.0, parts=.5, warp=0.0, hue=0.0, vig=.35, con=1.15),
	'tunnel': dict(fb=.88, trail=1.2, zoom=1.045, rot=.002, kal=0.0, seg=6, bloom=.4, ca=.004, parts=1.0, warp=.15, hue=.004, vig=.6, con=1.1),
	'prism':  dict(fb=.86, trail=.7, zoom=1.01, rot=.008, kal=1.0, seg=8, bloom=.35, ca=.003, parts=1.2, warp=.2, hue=.006, vig=.45, con=1.1),
	'storm':  dict(fb=.9, trail=1.0, zoom=.96, rot=-.012, kal=0.0, seg=6, bloom=.6, ca=.006, parts=2.6, warp=1.2, hue=.01, vig=.55, con=1.2),
}
CYCLE = ['tunnel', 'prism', 'storm']

def direct(A, dt, B, on):
	D = S.setdefault('dir', dict(scene='clean', quiet=0.0, beats=0, lastDrop=-99, avg=0.0, ci=0))
	man = P('Scene')
	if man != 'auto': D['scene'] = man; return
	if not on: D['scene'] = 'clean'; return
	D['avg'] += (B - D['avg']) * min(1, dt / 8)
	D['quiet'] = D['quiet'] + dt if B < .22 else 0
	if D['quiet'] > 3: D['scene'] = 'clean'
	elif D['scene'] == 'clean' and B > .35:
		D['ci'] = (D['ci'] + 1) % len(CYCLE); D['scene'] = CYCLE[D['ci']]; D['beats'] = S['beats']
	if D['scene'] != 'clean' and S['beats'] - D['beats'] >= 32:
		D['ci'] = (D['ci'] + 1) % len(CYCLE); D['scene'] = CYCLE[D['ci']]; D['beats'] = S['beats']
	if B - D['avg'] > .22 and B > .55 and S['clock'] - D['lastDrop'] > 12:     # drop
		D['lastDrop'] = S['clock']; D['scene'] = 'storm'; D['beats'] = S['beats']; S['flash'] = 1.0

def hsv(h, s_, v): return colorsys.hsv_to_rgb(h % 1, s_, v)

def live(A, dt, lobeR, ring, asp, scale, B, tempo, on):
	S['clock'] += dt
	direct(A, dt, B, on)
	tgt = SCENES[S['dir']['scene']]
	C = S.setdefault('cur', dict(SCENES['clean']))
	kf = 1 - math.exp(-dt * .8)
	for key, v in tgt.items(): C[key] += (v - C[key]) * kf
	kick = A['kickEnv'] * on; r = P('Reactivity')
	S['flash'] *= math.exp(-dt * 6)
	colour = P('Colour')
	camOn = bool(P('Camera'))
	fp = k('fb_proc')
	setv(fp, 0, (min(.97, C['fb'] * P('Feedback')), C['zoom'] + kick * .02 * r, C['rot'] * (tempo if on else 1), C['hue'] if colour else 0))
	setv(fp, 1, (C['warp'] * (.5 + B), S['clock'], asp, .9 + A['kickEnv'] * .6))
	setv(fp, 2, (.7 * (.4 + B) if camOn else 0, S['hue'], 0, 0))
	po = k('post')
	fl = S['flash'] * (.55 if P('Strobe') else .12)
	setv(po, 0, (round(C['seg']), C['kal'] * P('Kaleido'), C['ca'] + kick * .006 * r, C['bloom'] * P('Bloom')))
	setv(po, 1, (C['vig'], 0.0, fl, S['clock']))            # zrno vypnuto: na průhledném plátně by dělalo závoj
	setv(po, 2, (asp, S['clock'] * .04 * (tempo if on else 1), C['con'], C['trail'] * P('Feedback')))
	k('cam').par.orthowidth = 2 * asp / scale
	kk = A['kickEnv'] * on
	emit = (.003 + B * .03 + kk * .12) * P('Particles') * C['parts']
	ps = k('psim')
	setv(ps, 0, (S['clock'], dt, emit, kk * r / 2))
	setv(ps, 1, (S['rot'], S['n2'], ring, lobeR))
	setv(ps, 2, (.12 + tempo * .08 + B * .2, .18 + B * .5, B, .22))
	if colour: cr, cg, cb = hsv(S['hue'] + .5, .6, 1)
	else: cr, cg, cb = .55, .68, 1.
	a = .35 + B * .5 + A['kickEnv'] * .4
	mp = k('mat_p').par
	mp.colorr, mp.colorg, mp.colorb = cr * a, cg * a, cb * a
