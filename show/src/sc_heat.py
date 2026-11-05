# SCÉNA HEAT 2.0 — milion bodů z cihlové mřížky stoupá v tepelném poli (podle supermarket sallad „Custom 3D particle system“)
# Z webu zůstává logika: tepelné pole = simplex šum přes cihly, kopák = vlna tepla ze středu, virbl = z náhodného místa.
# Nové: body mají životnost a vrací se do cihel, horké body se otáčí a zvětšují s hudbou (místo myši z videa).
import math, random

SHOW = '/project1/show'
H = '/project1/show/heat'
S = {}

def P(name): return getattr(op(SHOW).par, name).eval()
def h(name): return op(H + '/' + name)

def num(x):
	# TD 2025.33230 převádí subnormální čísla (např. doznívající záblesk 5e-324) na 1.8e308 → bílý obraz; NaN/inf taky pryč
	x = float(x)
	return 0.0 if x != x or abs(x) < 1e-12 or abs(x) > 1e12 else x

def setv(o, i, v):
	p = o.par
	getattr(p, 'vec%dvaluex' % i).val, getattr(p, 'vec%dvaluey' % i).val = num(v[0]), num(v[1])
	getattr(p, 'vec%dvaluez' % i).val, getattr(p, 'vec%dvaluew' % i).val = num(v[2]), num(v[3])

def add_wave(x, y, amp):
	S['waves'].append([x, y, 0.0, amp]); S['waves'] = S['waves'][-4:]

def update(A, dt, now):
	if not S: S.update(dict(t=0.0, waves=[], idle=0.0, rot=0.0, rotV=0.0, scale=0.0, gate=.55, colorMix=0.0))
	on = A['on']; R = P('Reactivity'); b = A['bands']; B = A['busy'] if on else 0
	asp = 16 / 9
	S['t'] += dt * (.5 + (A['energy'] * 1.2 + b['mid'] * .6) * R * on)
	if A['kickHit']: add_wave(0.0, 0.0, (.5 + A['kickHit'] * .6) * R)
	if A['snareHit']:
		add_wave(random.uniform(-asp * .8, asp * .8), random.uniform(-.8, .8), (.4 + A['snareHit'] * .5) * R)
		S['rotV'] += (1 if random.random() < .5 else -1) * A['snareHit'] * .8 * R
	if not on:
		S['idle'] -= dt
		if S['idle'] <= 0: add_wave(random.uniform(-1.2, 1.2), random.uniform(-.7, .7), .6); S['idle'] = random.uniform(1.5, 3.)
	for w in S['waves']: w[2] += dt
	S['waves'] = [w for w in S['waves'] if w[2] < 3]
	S['rotV'] *= math.exp(-dt * 1.5)
	S['rot'] += dt * (S['rotV'] + (b['low'] * .3 * R * on))                  # místo myši z videa: basy točí horkými body
	S['scale'] += ((b['sub'] * .25 + A['kickEnv'] * .2) * R * on - S['scale']) * (1 - math.exp(-dt * 6))
	gt = (.5 - B * .2) if on else .5                                       # tichá hudba = víc studených (tmavých) cihel
	S['gate'] += (gt - S['gate']) * (1 - math.exp(-dt * 1.5))
	S['colorMix'] += ((1 if P('Colour') else .35) - S['colorMix']) * (1 - math.exp(-dt * 2))
	sim = h('sim')
	setv(sim, 0, (S['t'], dt, 1.0 / max(.5, P('Hlife')), P('Hflow') * (1 + B)))
	setv(sim, 1, (P('Hrise') * (1 + A['energy'] * .5 * R * on), 1.25 + A['energy'] * .4 * on, S['gate'], 1.6))
	setv(sim, 2, (S['rot'], S['scale'], S['colorMix'], P('Hbright')))
	setv(sim, 3, (A['energy'], A['kickEnv'] * on, 0, 0))
	for i in range(4):
		setv(sim, 4 + i, S['waves'][i] if i < len(S['waves']) else (0, 0, 0, 0))
	setv(h('start'), 0, (P('Hrows'), asp, .24, 0))
	rend = h('render')
	setv(h('mat'), 0, (P('Hsize'), rend.width, rend.height, 0))
