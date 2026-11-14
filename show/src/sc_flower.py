# SCÉNA KVĚT — skutečná lilie z časosběru (Mixkit 34700) ve 3D okně ve zdi (anamorfní iluze jako billboardy v New Yorku).
# 64 fází rozkvětu je v Texture 3D, hudba volí fázi: v tichu se lilie zavře do pupenu hluboko ve výklenku,
# s energií rozkvete a vyleze z okna před zeď — přeroste rám, svítí na zeď kolem a vrhá stín do výklenku.
# Kopák ji „nadechne“ a rozsvítí hrany výklenku, okraj růstu (kde právě raší) se rozsvítí na hi-hatech.
import math

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

def window(w, A, on, obj, edgePulse, hue):
	"""společné nastavení 3D okna (stejné jako v sc_bird.py); obj = (x, y, z, poloviční výška karty, poměr stran)"""
	asp = w.width / max(1, w.height)
	H = P('Wsize'); W = min(asp * .92, H * 1.5); oy = -.08
	setv(w, 0, (0, P('Weye'), P('Wdist') * 2, asp))
	setv(w, 1, (W, H, P('Wdepth'), P('Wedges') * (.35 + A['energy'] * .4 * on)))
	setv(w, 2, obj[:4])
	setv(w, 3, (obj[4], .4, oy + H + .7, 1.6))
	setv(w, 4, (hue, P('Wgrid'), P('Wrefl'), P('Wshadow')))
	setv(w, 5, (edgePulse, P('Wlight'), 1.0, oy))
	return H, oy

def update(A, dt, now):
	if 'bloom' not in S:
		S.update(dict(t=0.0, bloom=.2, kickP=0.0, hue=.08, z=-.6, zv=0.0))
	preload()
	on = A['on']; R = P('Reactivity'); B = A['busy'] if on else 0
	S['t'] += dt
	if A['kickHit'] and on: S['kickP'] = max(S['kickP'], (.05 + A['kickHit'] * .08) * R)
	S['kickP'] *= math.exp(-dt * 6.0)
	# rozkvět: ticho = pupen, energie a hutnost = rozvitá lilie
	tgt = (.15 + A['energy'] * .35 + B * .55) * P('Fbloom') if on else (.35 + .3 * math.sin(S['t'] * .25))
	S['bloom'] += (min(1.0, tgt) - S['bloom']) * (1 - math.exp(-dt * (3.0 if tgt > S['bloom'] else .8)))
	bloom = S['bloom']
	S['hue'] += dt * (.01 + A['centroid'] * .03 * on)
	g = f('lily')
	setv(g, 0, (bloom, S['kickP'], (.4 + A['hatEnv'] * on * 1.8) * R, 0))
	setv(g, 1, (.5, .5, .32, 12))
	setv(g, 2, (0, 9, 0, 0))
	setv(g, 3, (1, 1, P('Fbright'), 1))
	for i in range(3): setv(g, 4 + i, tuple((A['LOB'] if on else [.4] * 12)[4 * i:4 * i + 4]))
	# vylézání z okna: pupen hluboko ve výklenku, rozkvetlá lilie před zdí; pružina, kopák ji postrčí dopředu
	D = P('Wdepth'); pop = P('Wpop')
	zt = -D * .6 + (bloom * 1.0 + B * .3) * pop * (D * .6 + .7)
	S['zv'] += ((zt - S['z']) * 6.0 - S['zv'] * 4.5) * dt + A['kickHit'] * .35 * R * pop * on
	S['z'] += S['zv'] * dt
	hh = 1.1 * P('Fsize') * P('Wsize')
	H, oy = P('Wsize'), -.08
	cy = oy - H + hh * .7 + .03 * math.sin(S['t'] * .4)           # lilie stojí na podlaze výklenku, jemně se pohupuje
	window(f('window'), A, on, (.04 * math.sin(S['t'] * .23), cy, S['z'], hh, 1.0), A['kickEnv'] * on, S['hue'])

def look_name(): return 'okno'
