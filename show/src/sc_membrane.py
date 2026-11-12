# SCÉNA MEMBRÁNA — přes obraz je napnuté plátno a zezadu se do něj tlačí ruce, chodidla a obličej podle hudby.
# Části těla jsou skutečné 3D modely (show/assets, viz src/tools/make_body_parts.py); hloubka jejich povrchu
# se změní na napnutí látky (src/glsl/membrane_*.glsl).
#   kopák  → dlaň (při plné hudbě občas chodidlo) prudce udeří do plátna, plátno se rozvibruje
#   virbl  → druhá ruka, menší dotek
#   držené tóny / zpěv → zezadu se pomalu vynoří obličej
#   ticho  → ruka se pomalu přitiskne a táhne plátno do strany
import math, random

SHOW = '/project1/show'
M = '/project1/show/membrane'
SLOTS = 6
PARTS = {'hand': 0, 'foot': 1, 'face': 2}
SCALE = {'hand': .78, 'foot': .9, 'face': 1.15}
FRONT = {'hand': .2, 'foot': .3, 'face': .22}          # jak daleko před střed dílu je plocha, která se opře o plátno (dlaň, chodidlo, obličej — ne palec)
TILT = {'hand': -12., 'foot': 0., 'face': 0.}          # ruka v klidové póze ohýbá prsty dozadu → naklonit, ať se do plátna opře celá dlaň
HIDDEN = -.8
S = {}

def P(name): return getattr(op(SHOW).par, name).eval()
def m(name): return op(M + '/' + name)

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
	S.update(dict(actors=[dict(part='hand', x=0., y=0., rot=0., mir=1, depth=HIDDEN, target=HIDDEN, speed=4., hold=0.,
		state='idle', age=0., vx=0., vy=0.) for _ in range(SLOTS)], idle=1.0, faceCool=0.0, hue=random.random(),
		light=.6, lightV=0.0, flash=0.0, impulses=[]))

def allowed(part):
	return bool(P({'hand': 'Mhands', 'foot': 'Mfeet', 'face': 'Mfaces'}[part]))

def spawn(part, depth, speed, hold, drift=0.0, x=None, y=None):
	"""pošle díl do plátna; použije volný slot, jinak ten, který je venku nejdéle"""
	if not allowed(part):
		if part == 'hand' or not allowed('hand'): return None
		part = 'hand'
	asp = 16 / 9
	free = [a for a in S['actors'] if a['state'] == 'idle']
	a = free[0] if free else max(S['actors'], key=lambda a: a['age'])
	a.update(part=part, state='in', target=depth, speed=speed, hold=hold, age=0.0,
		x=x if x is not None else random.uniform(-asp * .72, asp * .72),
		y=y if y is not None else random.uniform(-.6, .6),
		rot=random.uniform(-40, 40) if part != 'face' else random.uniform(-12, 12),
		mir=random.choice((-1, 1)), vx=random.uniform(-drift, drift), vy=random.uniform(-drift, drift) * .5)
	if a['depth'] < HIDDEN * .5: a['depth'] = HIDDEN * .6               # začíná kousek za plátnem
	return a

def kick_impulse(a, amp):
	asp = 16 / 9
	S['impulses'].append((a['x'] / (2 * asp) + .5, a['y'] / 2 + .5, amp, .12))

def update(A, dt, now):
	if not S: reset()
	on = A['on']; R = P('Reactivity'); b = A['bands']; B = A['busy'] if on else 0
	act = P('Mactivity')
	S['impulses'] = []
	# ── události z hudby ──
	if on:
		if A['kickHit'] and random.random() < .55 + .45 * min(1, act):
			k = A['kickHit']
			part = 'foot' if (B > .55 and random.random() < .35) else 'hand'
			a = spawn(part, (.11 + .09 * k) * R, 16 + 8 * k, random.uniform(.3, .8))       # látka obtiskne jen přední stranu
			if a: kick_impulse(a, .12 * k * R)
			S['flash'] = max(S['flash'], k * .5)
		if A['snareHit'] and random.random() < .4 * act:
			a = spawn('hand', (.08 + .07 * A['snareHit']) * R, 12, random.uniform(.2, .5), drift=.1)
			if a: kick_impulse(a, .07 * A['snareHit'] * R)
			S['lightV'] += random.choice((-1, 1)) * A['snareHit'] * 2
		S['faceCool'] -= dt
		singing = A['sustain'] > .45 or (b['mid'] > .6 and A['kickEnv'] < .2)
		if singing and S['faceCool'] <= 0 and not any(x['part'] == 'face' and x['state'] != 'idle' for x in S['actors']):
			spawn('face', .15 * R, 1.3, random.uniform(2.5, 5.0), drift=.02, x=random.uniform(-.8, .8), y=random.uniform(-.25, .2))
			S['faceCool'] = 8.0
	else:                                                                 # ticho: pomalé tlačení a tažení plátna
		S['idle'] -= dt
		if S['idle'] <= 0:
			part = random.choice(['hand', 'hand', 'hand', 'face', 'foot'])
			spawn(part, random.uniform(.1, .16), 1.4, random.uniform(1.5, 3.0), drift=.18)
			S['idle'] = random.uniform(1.5, 3.5) / max(.2, act)
	# ── pohyb dílů ──
	for i, a in enumerate(S['actors']):
		a['age'] += dt
		if a['state'] == 'in':
			if a['depth'] >= a['target'] - .01: a['state'] = 'hold'
		elif a['state'] == 'hold':
			a['hold'] -= dt
			if a['part'] == 'face' and on and A['sustain'] > .45: a['hold'] = max(a['hold'], .3)   # obličej drží, dokud zpěv drží tón
			if a['hold'] <= 0: a['state'] = 'out'; a['target'] = HIDDEN; a['speed'] = 2.5 if a['part'] == 'face' else 5
		elif a['state'] == 'out' and a['depth'] <= HIDDEN + .05:
			a['state'] = 'idle'
		k = 1 - math.exp(-dt * a['speed'])
		a['depth'] += (a['target'] - a['depth']) * k
		if a['state'] in ('in', 'hold'):                                  # ruce táhnou plátno do strany
			a['x'] += a['vx'] * dt; a['y'] += a['vy'] * dt
		g = m('a%d' % i)
		sc = SCALE[a['part']]
		pp = g.par
		pp.tx, pp.ty = a['x'], a['y']
		pp.tz = a['depth'] - FRONT[a['part']] * sc
		pp.rx = TILT[a['part']]; pp.rz = a['rot']
		pp.sx, pp.sy, pp.sz = sc * a['mir'], sc, sc
		g.op('pick').par.input = PARTS[a['part']]
	# ── plátno ──
	imp = S['impulses'][:4]
	for i in range(4):
		setv(m('wave'), 1 + i, imp[i] if i < len(imp) else (0, 0, 0, 0))
	setv(m('wave'), 0, (.3, .965, 0, 0))
	S['flash'] *= math.exp(-dt * 6)
	S['lightV'] *= math.exp(-dt * 2)
	S['light'] += dt * (.15 + S['lightV'])
	S['hue'] += dt * (.015 + (A['centroid'] * .05 + B * .05) * on)
	setv(m('shade'), 0, (P('Mbump'), .8 * P('Mtent'), .25 * P('Mwave'), P('Mbright')))
	setv(m('shade'), 1, (S['hue'], .55 + A['energy'] * .4 * on, S['light'], S['flash']))
	setv(m('shade'), 2, (b['low'] * on, b['mid'] * on, b['air'] * on, A['energy'] * on))
