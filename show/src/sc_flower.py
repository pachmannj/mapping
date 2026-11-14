# SCÉNA KVĚT — skutečná lilie z časosběru (Mixkit 34700) ve 3D okně ve zdi (anamorfní iluze jako billboardy v New Yorku).
# 64 fází rozkvětu je v Texture 3D, hudba volí fázi: v tichu se lilie zavře do pupenu hluboko ve výklenku,
# s energií rozkvete a vyleze z okna před zeď — přeroste rám, svítí na zeď kolem a vrhá stín do výklenku.
# Kopák ji „nadechne“ a rozsvítí hrany výklenku, okraj růstu (kde právě raší) se rozsvítí na hi-hatech.
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

def window(w, A, on, obj, edgePulse, hue, wall=1.0, wallY=0.0):
	"""společné nastavení 3D okna (stejné jako v sc_bird.py); obj = (x, y, z, poloviční výška karty, poměr stran)"""
	asp = w.width / max(1, w.height)
	H = P('Wsize'); W = min(asp * .92, H * 1.5); oy = -.08
	setv(w, 0, (0, P('Weye'), P('Wdist') * 2, asp))
	setv(w, 1, (W, H, P('Wdepth'), P('Wedges') * (.35 + A['energy'] * .4 * on)))
	setv(w, 2, obj[:4])
	setv(w, 3, (obj[4], .4 if P('Wbox') else 1.1, oy + H + .7, 1.6))
	setv(w, 4, (hue, P('Wgrid'), P('Wrefl'), P('Wshadow')))
	setv(w, 5, (edgePulse, P('Wlight'), 1.0, oy))
	setv(w, 6, (1 if P('Wbox') else 0, P('Wwall') * wall, 1.15, wallY))
	return H, oy

def dev(key, x, dt, tau=4.0):
	"""odchylka od klouzavého průměru: reaguje na každou změnu v hudbě, ne na celkovou hlasitost"""
	m = S.setdefault('avg_' + key, x)
	S['avg_' + key] = m + (x - m) * min(1.0, dt / tau)
	return x - m

def update(A, dt, now):
	if 'bloom' not in S:
		S.update(dict(t=0.0, bloom=.2, kickP=0.0, hue=.08, z=.2, zv=0.0, sc=1.0, scv=0.0, fl=0.0, lx=0.0, lxv=0.0))
	preload()
	on = A['on']; R = P('Reactivity'); B = A['busy'] if on else 0; b = A['bands']
	S['t'] += dt
	# rychlé reakce: kopák lilii nadechne (fáze dopředu), pružně ji vystrčí a zvětší, rozsvítí ji i zeď
	if A['kickHit'] and on:
		S['kickP'] = max(S['kickP'], (.1 + A['kickHit'] * .16) * R)
		S['zv'] += A['kickHit'] * 1.0 * R * P('Wpop'); S['scv'] += A['kickHit'] * 1.4 * R; S['fl'] = max(S['fl'], A['kickHit'])
	if A['snareHit'] and on:
		S['scv'] -= A['snareHit'] * .7 * R; S['lxv'] += random.choice((-1, 1)) * A['snareHit'] * .6 * R
	S['kickP'] *= math.exp(-dt * 7.0); S['fl'] *= math.exp(-dt * 6.0)
	# rozkvět: dlouhodobá energie otevře květ, každá změna v hudbě (odchylka od průměru) s ním hne hned
	e = A['energy']
	tgt = ((.12 + e * .4 + B * .35 + dev('e', e, dt) * 1.6 + dev('low', b['low'], dt, 2.0) * .6 + A['kickEnv'] * .15) * P('Fbloom')
		if on else (.35 + .3 * math.sin(S['t'] * .25)))
	tgt = max(.14, min(1.0, tgt))
	S['bloom'] += (tgt - S['bloom']) * (1 - math.exp(-dt * (10.0 if tgt > S['bloom'] else 3.0)))
	bloom = S['bloom']
	S['hue'] += dt * (.01 + A['centroid'] * .03 * on)
	g = f('lily')
	setv(g, 0, (bloom, S['kickP'], (.5 + A['hatEnv'] * on * 2.5) * R, 0))
	setv(g, 1, (.5, .5, .32, 12))
	setv(g, 2, (0, 9, 0, 0))
	setv(g, 3, (1, 1, P('Fbright') * (.85 + S['fl'] * .25 + A['snareEnv'] * .1 * on), 1))
	for i in range(3): setv(g, 4 + i, tuple((A['LOB'] if on else [.4] * 12)[4 * i:4 * i + 4]))
	box = P('Wbox'); D = P('Wdepth'); pop = P('Wpop'); H = P('Wsize'); oy = -.08
	# hloubka: s výklenkem z něj vylézá, bez výklenku visí před zdí a s hudbou se k divákovi přibližuje (stín se vzdaluje)
	if box: zt = -D * .6 + (bloom * 1.0 + B * .3) * pop * (D * .6 + .7)
	else:   zt = .1 + (bloom * .3 + B * .12 + dev('e2', e, dt, 1.5) * .5) * pop
	S['zv'] += ((zt - S['z']) * 9.0 - S['zv'] * 5.0) * dt
	S['z'] += S['zv'] * dt
	S['scv'] += ((1.0 - S['sc']) * 30.0 - S['scv'] * 7.0) * dt; S['sc'] += S['scv'] * dt * .12
	S['lxv'] += (-S['lx'] * 14.0 - S['lxv'] * 5.0) * dt; S['lx'] += S['lxv'] * dt * .1
	if box:
		hh = 1.1 * P('Fsize') * H * S['sc']
		cy = oy - H + hh * .7 + .03 * math.sin(S['t'] * .4)        # lilie stojí na podlaze výklenku
	else:
		hh = .78 * P('Fsize') * S['sc']
		cy = .02 + .03 * math.sin(S['t'] * .4)
	wall = .55 + e * .3 * on + S['fl'] * .5
	window(f('window'), A, on, (S['lx'] + .04 * math.sin(S['t'] * .23), cy, S['z'], hh, 1.0), A['kickEnv'] * on, S['hue'], wall, cy + .1)

def look_name(): return 'okno'
