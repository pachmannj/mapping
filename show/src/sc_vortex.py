# SCÉNA VORTEX 2.0 — organismus ze statisíců POP částic zrozených ze zvukové vlny (podle nicholaspjm „Audio Reactive Particles using POPs“)
# Logika chování je z webového Vortex Organism; síly počítá GLSL POP v src/glsl/vortex_forces.glsl.
# Stavový automat chování (drift / tension / flare / fragment / reform) řízený nástroji, kamera obíhá kolem.
import math, random

SHOW = '/project1/show'
V = '/project1/show/vortex'
S = {}
NAMES = ['drift', 'tension', 'flare', 'fragment', 'reform']

def P(name): return getattr(op(SHOW).par, name).eval()
def v(name): return op(V + '/' + name)

def num(x):
	# TD 2025.33230 převádí subnormální čísla (např. doznívající záblesk 5e-324) na 1.8e308 → bílý obraz; NaN/inf taky pryč
	x = float(x)
	return 0.0 if x != x or abs(x) < 1e-12 or abs(x) > 1e12 else x

def setv(o, i, val):
	p = o.par
	getattr(p, 'vec%dvaluex' % i).val, getattr(p, 'vec%dvaluey' % i).val = num(val[0]), num(val[1])
	getattr(p, 'vec%dvaluez' % i).val, getattr(p, 'vec%dvaluew' % i).val = num(val[2]), num(val[3])

def ss(a, b, x):
	x = max(0.0, min(1.0, (x - a) / (b - a))); return x * x * (3 - 2 * x)

def reset():
	S.clear()
	S.update(dict(time=0.0, blend=[1., 0., 0., 0., 0.], cur=0, stateTime=0.0, intensity=0.0, warmth=0.0, auto=0.0,
		cp=0.0, cspeed=1.0, density=1.1, turb=.8, bright=1.4, camA=0.0, camY=0.0, rhythm=0.0,
		s=dict(kick=0., snare=0., vocal=0., hihat=0., cymbal=0., sub=0., bass=0., trans=0.), prev={}, energyP=0.0, sustT=0.0, sust=0.0))

def k(dt, f): return 1 - (1 - f) ** (dt * 60)     # vyhlazení nezávislé na snímkové frekvenci

def to(st):
	if st != S['cur']: S['cur'] = st; S['stateTime'] = 0.0

def update(A, dt, now):
	if not S: reset()
	S['time'] += dt; t = S['time']
	S['stateTime'] += dt
	on = A['on']
	s = S['s']; pv = S['prev']; on1 = 1 if on else 0
	# ── analýza: reaguje na ZMĚNY (údery, výkyvy pásem proti vlastnímu průměru), ne na hlasitost.
	#    Podle hlasitosti by u elektra (basy pořád naplno) zůstala hustota i komprese na maximu → koule bez pohybu.
	b_ = A['bands']; avg = S.setdefault('avg', {})
	def dev(name, val, tau=2.5):
		a_ = avg.get(name, val); avg[name] = a_ + (val - a_) * (1 - math.exp(-dt / tau))
		return max(0., min(1., (val - a_) * 2.5))
	x = dict(kick=A['kickEnv'], snare=A['snareEnv'], hihat=A['hatEnv'], cymbal=dev('air', b_['air']),
	         vocal=dev('mid', b_['mid'], 4.), sub=dev('sub', b_['sub']))
	x = {n: val * on1 for n, val in x.items()}
	kickT = A['kickHit'] * 1.2 * on1
	snareT = A['snareHit'] * on1
	hihatT = (.6 if A['hats'] != pv.get('hats', A['hats']) else 0.) * on1; pv['hats'] = A['hats']
	energy = (.05 + dev('energy', A['energy'], 3.) * .15 + A['kickEnv'] * .1 + A['busy'] * .05) * on1
	trans = max(0., (energy - S['energyP']) * 4); S['energyP'] = energy
	S['rhythm'] += (.2 + energy * 4) * dt * on1
	S['sust'] = A['sustain'] * on1
	for n, f in (('kick', .5), ('snare', .45), ('vocal', .35), ('hihat', .5), ('cymbal', .45), ('sub', .4)):
		s[n] += (x[n] - s[n]) * k(dt, f)
	s['bass'] += ((s['sub'] + s['kick']) * .5 - s['bass']) * k(dt, .4); s['trans'] += (trans - s['trans']) * k(dt, .5)
	# ── autonomní cyklus (běží i bez zvuku) ──
	S['cp'] += dt * .025 * S['cspeed']
	if S['cp'] >= 1: S['cp'] -= 1; S['cspeed'] = .7 + random.random() * .7
	cp = S['cp']
	if cp < .55: autoI = .08 + .17 * ss(0, .55, cp)
	elif cp < .7: autoI = .25 + .55 * ss(.55, .7, cp)
	elif cp < .78: autoI = .8 + .2 * ss(.7, .78, cp)
	elif cp < .88: autoI = 1 - .65 * ss(.78, .88, cp)
	else: autoI = .35 - .27 * ss(.88, 1, cp)
	S['auto'] = autoI * .05 if on else autoI
	v0 = (math.sin(t * .13) * 1.2, math.cos(t * .19) * .4, math.cos(t * .11) * 1.0, 0)
	v1 = (math.cos(t * .17) * 1.5, math.sin(t * .23) * .3, math.sin(t * .29) * 1.3, 0)
	v2 = (math.sin(t * .31) * .8, math.cos(t * .37) * .5, math.cos(t * .41) * .9, 0)
	cc = (math.sin(t * .13) * 1.2 + math.sin(t * .31) * .5, math.cos(t * .17) * .6, math.cos(t * .11) * 1.0 + math.sin(t * .23) * .4, 0)
	tI = min(1., energy * 4.) if on else autoI
	S['intensity'] += (tI - S['intensity']) * k(dt, .4 if tI > S['intensity'] else .15)
	comp = s['sub'] * 1.2 + kickT + s['trans'] if on else autoI
	# ── přechody stavů podle nástrojů ──
	cur, st = S['cur'], S['stateTime']
	if on:
		if kickT > .12 and cur != 2: to(2)
		elif snareT > .1 and cur == 0: to(1)
		elif energy < .04 and st > .6 and cur != 0: to(0)
		elif S['sust'] > .5 and cur < 1: to(1)
		elif cur == 2 and st > .4 and s['kick'] < .2: to(3)
		elif cur == 3 and st > .6: to(4)
		elif cur == 4 and st > .8: to(0)
	else:
		to(0 if cp < .55 else 1 if cp < .7 else 2 if cp < .78 else 3 if cp < .88 else 4)
	if on:
		tw = s['kick'] * 1.5 + kickT + snareT + s['sub'] - s['hihat'] * .6 - s['cymbal'] * .8 - S['sust'] * .3
		tw = max(0., min(1., tw)); ws = .45 if tw > S['warmth'] else .1
	else:
		tw = [0, .3, 1., .7, .1][S['cur']]; ws = .03
	S['warmth'] += (tw - S['warmth']) * k(dt, ws)
	bs = .12 if on else (.02 if S['cur'] == 0 else .04)
	for i in range(5): S['blend'][i] += ((1. if i == S['cur'] else 0.) - S['blend'][i]) * k(dt, bs)
	# ── automatické parametry ──
	R = P('Reactivity')
	if on:
		td_ = .9 + s['kick'] * .8 + S['sust'] * .4 + energy * .3
		S['density'] = max(.5, min(2.5, S['density'] + (td_ - S['density']) * k(dt, .2)))
		tt = .4 + s['hihat'] * 2 + s['cymbal'] * 2 + s['snare'] * 1.5 + energy * 2
		S['turb'] = max(.2, min(3., S['turb'] + (tt - S['turb']) * k(dt, .2)))
		tb = .9 + kickT * 1.5 + snareT + s['hihat'] * .5 + S['sust'] * .4 + energy * 1.5
		S['bright'] = max(.5, min(3., S['bright'] + (tb - S['bright']) * k(dt, .4 if tb > S['bright'] else .06)))
	else:
		S['density'] += (1.1 - S['density']) * k(dt, .02); S['turb'] += (.8 - S['turb']) * k(dt, .02); S['bright'] += (1.4 - S['bright']) * k(dt, .02)
	f = v('geo/forces'); B = S['blend']                       # GLSL POP se silami uvnitř smyčky Particle POP
	setv(f, 0, (t, dt, energy, s['trans']))
	setv(f, 1, (s['kick'], s['snare'], s['hihat'], s['cymbal']))
	setv(f, 2, (s['vocal'], s['sub'], S['sust'], S['rhythm']))
	setv(f, 3, (kickT, snareT, hihatT, S['auto']))
	setv(f, 4, (S['turb'] * P('Vturb'), S['density'], R, comp))
	setv(f, 5, (B[0], B[1], B[2], B[3]))
	setv(f, 6, (B[4], S['warmth'], S['intensity'], S['bright'] * P('Vbright') * .5))
	setv(f, 7, v0[:3] + (P('Vsize'),)); setv(f, 8, v1); setv(f, 9, v2); setv(f, 10, cc)
	lob = A['LOB'] if on else [.35] * 12                      # jako Krasohled: 12 pásem vyboulí organismus ve 12 směrech
	setv(f, 11, tuple(lob[0:4])); setv(f, 12, tuple(lob[4:8])); setv(f, 13, tuple(lob[8:12]))
	# ── zrod částic ze zvukové vlny: víc hudby = víc částic ──
	pp = v('geo/particles').par
	if not S.get('started'):                                  # simulaci spustí až aktivní scéna (po nastavení uniform)
		S['started'] = True
		pp.play = True; pp.initializepulse.pulse(); pp.startpulse.pulse()
	pp.maxparticles = int(P('Vcount'))
	pp.birthrate = P('Vcount') / 4.0 * P('Vbirth') * (.35 + (energy * 1.5 + kickT * .5) * on)
	# ── kamera ──
	S['camV'] = S.get('camV', 0.) * math.exp(-dt * 1.5) + (kickT * .25 + snareT * .15) * (1 if S.get('camDir', 1) > 0 else -1)
	if snareT and random.random() < .3: S['camDir'] = -S.get('camDir', 1)                # virbl občas otočí směr
	S['camA'] += dt * (.015 + s['vocal'] * .08 + S['camV'])
	S['camY'] += (math.sin(t * .1) * .6 + (s['cymbal'] - s['sub']) * .8 - S['camY']) * k(dt, .03)
	r = (4.2 + math.sin(t * .08) * .3 - s['kick'] * .6 - S['intensity'] * .4) * P('Vzoom')
	c = v('cam').par
	c.tx, c.ty, c.tz = math.cos(S['camA']) * r, S['camY'], math.sin(S['camA']) * r
	v('fb_lvl').par.opacity = min(.93, .85 * P('Vtrails') * (1 - S['blend'][2] * .25))
	setv(v('compose'), 0, (S['bright'] * .7, S['warmth'], t, S['intensity']))

def state_name(): return NAMES[S['cur']] if S else ''
