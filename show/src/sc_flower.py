# SCÉNA KVĚT — skutečná lilie z časosběru (Mixkit 34700): 64 fází rozkvětu je v Texture 3D, hudba volí fázi.
# Z fází se jednou spočítá mapa času příchodu (kdy do kterého pixelu květ doroste) — z ní žijí netradiční looky.
# Vnitřní režisér střídá looky (klid = reál, plná hudba a dropy = netradiční):
#   real    lilie rozkvétá s energií, kopák ji „nadechne“, okraj růstu se rozsvítí na hi-hatech
#   map     mapa času: vrstevnice růstu květu, každá svítí podle svého pásma, kopák pošle vlnu od pupenu ven
#   sculpt  časová socha: celý rozkvět jako svítící 3D objem (čas = hloubka), vrstva „teď“ je pevná
#   flow    proudy růstu: barva teče z rašícího okraje ve směru, kterým květ rostl, a za lístky ven do prostoru
import math, random

SHOW = '/project1/show'
Fc = '/project1/show/flower'
FRAMES = 64
S = {}

def P(name): return getattr(op(SHOW).par, name).eval()
def f(name): return op(Fc + '/' + name)

def num(x):
	# TD 2025.33230 převádí subnormální čísla (např. doznívající záblesk 5e-324) na 1.8e308 → bílý obraz; NaN/inf taky pryč
	x = float(x)
	return 0.0 if x != x or abs(x) < 1e-12 or abs(x) > 1e12 else x

def setv(o, i, v):
	p = o.par
	getattr(p, 'vec%dvaluex' % i).val, getattr(p, 'vec%dvaluey' % i).val = num(v[0]), num(v[1])
	getattr(p, 'vec%dvaluez' % i).val, getattr(p, 'vec%dvaluew' % i).val = num(v[2]), num(v[3])

def preload():
	"""jednou po startu: nahraje 64 fází rozkvětu do Texture 3D (4 snímky na fázi, ~4 s, scéna nemusí být aktivní).
	Průběžné nahrávání Texture 3D musí být vypnuté (Active = off), jinak přepisuje vrstvy od začátku."""
	if S.get('loaded'): return
	S['loaded'] = True
	src, t = f('frame_src'), f('phases')
	t.par.active = False; t.par.resetpulse.pulse()
	for k in range(FRAMES):
		run("op(%r).par.file = %r" % (src.path, 'media/lily/f_%02d.jpg' % (k + 1)), delayFrames=4 * k + 2)
		run("t = op(%r); t.par.replaceindex = %d; t.par.replacesinglepulse.pulse(); t.cook(force=True)" % (t.path, k), delayFrames=4 * k + 5)

LOOKS = {
	'real':   dict(real=1.0, map=0.0, sculpt=0.0, flow=0.0),
	'map':    dict(real=0.0, map=1.0, sculpt=0.0, flow=0.0),
	'sculpt': dict(real=0.0, map=0.0, sculpt=1.0, flow=0.0),
	'flow':   dict(real=.85, map=0.0, sculpt=0.0, flow=1.0),
}
CALM, WILD = ['real', 'flow'], ['map', 'sculpt', 'flow']

def direct(A, dt, now, on, B):
	man = P('Flook')
	if man != 'auto': S['look'] = man; return
	S['avgB'] += (B - S['avgB']) * min(1.0, dt / 8)
	S['lookT'] += dt
	ab = P('Fabstract')
	def pick(wild):
		pool = [l for l in (WILD if wild else CALM) if l != S['look']] or (WILD if wild else CALM)
		S['look'] = random.choice(pool); S['lookBeat'] = S['beats']; S['lookT'] = 0.0
	if on:
		if B - S['avgB'] > .2 and B > .55 and now - S['lastDrop'] > 15:
			S['lastDrop'] = now; pick(random.random() < .4 + ab * .6)
		elif S['beats'] - S['lookBeat'] >= 32 or (S['lookT'] > 25 and S['beats'] - S['lookBeat'] < 2):
			pick(random.random() < ab * (.25 + B * .75))
		elif B < .2 and S['look'] in WILD and S['look'] not in CALM and S['lookT'] > 4:
			pick(False)
	elif S['lookT'] > 14:
		pick(random.random() < ab * .5)

def update(A, dt, now):
	if 'look' not in S:
		S.update(dict(t=0.0, bloom=.2, wave=9.0, waveA=0.0, beats=0, look='real', lookBeat=0, lookT=0.0, avgB=0.0, lastDrop=-99.0,
			hue=0.0, flowP=0.0, kickP=0.0, depth=.4, burst=0.0, W=dict(LOOKS['real'])))
	preload()
	on = A['on']; R = P('Reactivity'); B = A['busy'] if on else 0; FX = P('Fspread') * R
	S['t'] += dt
	tempo = A['tempo'] if (on and A['bpm']) else 1
	if A['kickHit'] and on:
		S['beats'] += 1; S['wave'] = 0.0; S['waveA'] = (.5 + A['kickHit'] * .8) * FX
		S['kickP'] = max(S['kickP'], (.06 + A['kickHit'] * .1) * R); S['burst'] = max(S['burst'], A['kickHit'] * .6 * FX)
	S['wave'] += dt * (.5 + tempo * .5)
	S['waveA'] *= math.exp(-dt * 1.5)
	S['kickP'] *= math.exp(-dt * 6.0)
	S['burst'] *= math.exp(-dt * 10.0)
	# rozkvět: ticho = pupen, energie a hutnost = rozvitá lilie
	tgt = (.15 + A['energy'] * .35 + B * .55) * P('Fbloom') if on else (.35 + .3 * math.sin(S['t'] * .25))
	S['bloom'] += (min(1.0, tgt) - S['bloom']) * (1 - math.exp(-dt * (3.0 if tgt > S['bloom'] else .8)))
	direct(A, dt, now, on, B)
	tl = LOOKS[S['look']]; W = S['W']; kf = 1 - math.exp(-dt * 1.4)
	for key, val in tl.items(): W[key] += (val - W[key]) * kf
	S['hue'] += dt * (.03 + (A['centroid'] * .15 + B * .15) * on)
	S['flowP'] += dt * (.25 + (A['energy'] * 1.2 + B * 1.5) * on) * tempo
	lob = A['LOB'] if on else [.4 + .25 * math.sin(S['t'] * .5 + i * .6) for i in range(12)]
	g = f('lily'); asp = g.width / max(1, g.height)
	zoom = P('Fzoom') * (1 + A['kickEnv'] * .025 * on)
	bloom = S['bloom']
	# reál + mapa času
	setv(g, 0, (bloom, S['kickP'], (.4 + A['hatEnv'] * on * 1.8) * FX, W['map']))
	setv(g, 1, (.5, .63, .32, 10 + 14 * B))
	setv(g, 2, (S['flowP'], S['wave'], S['waveA'], S['hue']))
	setv(g, 3, (zoom, W['real'], P('Fbright'), asp))
	for i in range(3): setv(g, 4 + i, tuple(lob[4 * i:4 * i + 4]))
	# časová socha: kamera stojí, jen velmi pomalu plyne; kopák sochu natáhne do hloubky
	S['depth'] += ((.5 + B * .3 + A['kickEnv'] * .2 * FX * on) - S['depth']) * (1 - math.exp(-dt * 6))
	v = f('vol')
	setv(v, 0, (bloom, S['depth'], .62 + .1 * math.sin(S['t'] * .05), W['sculpt']))
	setv(v, 1, (.5, .63, .36, asp))
	setv(v, 2, (S['hue'], min(1.0, .7 * FX), 1.0 + B * .6, P('Fbright') * 1.2))
	setv(v, 3, (.22, 12 - B * 5, P('Fzoom') * .78, 0))
	for i in range(3): setv(v, 4 + i, tuple(lob[4 * i:4 * i + 4]))
	# proudy růstu
	gr = f('grow')
	setv(gr, 0, (S['t'], (1.5 + A['energy'] * 2.5 + B * 3) * tempo * (on or .5), min(.99, .965 + B * .02), 1.2 * FX))
	setv(gr, 1, (.5, .63, 0, asp))
	setv(gr, 2, (zoom, bloom, W['flow'], S['burst']))
	setv(gr, 3, (.004 + .01 * B * FX, 0, 0, 0))
	setv(f('look'), 0, (W['flow'], P('Fbright'), 0, 0))

def look_name(): return S.get('look', '')
