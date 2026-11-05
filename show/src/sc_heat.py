# SCÉNA HEAT — cihlová mřížka (port z heat_ndex.html)
# kopák = vlna ze středu, virbl a hihat = vlny z náhodných míst, energie zrychluje a zostřuje šum
import math, random

SHOW = '/project1/show'
G = '/project1/show/heat/glsl'
S = {}

def P(name): return getattr(op(SHOW).par, name).eval()

def num(x):
	# TD 2025.33230 převádí subnormální čísla (např. doznívající záblesk 5e-324) na 1.8e308 → bílý obraz; NaN/inf taky pryč
	x = float(x)
	return 0.0 if x != x or abs(x) < 1e-12 or abs(x) > 1e12 else x

def setv(o, i, v):
	p = o.par
	getattr(p, 'vec%dvaluex' % i).val, getattr(p, 'vec%dvaluey' % i).val = num(v[0]), num(v[1])
	getattr(p, 'vec%dvaluez' % i).val, getattr(p, 'vec%dvaluew' % i).val = num(v[2]), num(v[3])

def add_pulse(x, y, amp):
	S['pulses'].append([x, y, 0.0, amp]); S['pulses'] = S['pulses'][-8:]

def update(A, dt, now):
	g = op(G); W, H = g.width, g.height
	if not S: S.update(dict(t=0.0, hue=random.random(), pulses=[], idle=0.0, gate=.35))
	on = A['on']; R = P('Reactivity'); b = A['bands']
	S['t'] += dt * (1 + (A['energy'] * 1.5 + b['mid'] * .8) * R if on else .8)
	if A['kickHit']: add_pulse(W * .5, H * .5, (.6 + A['kickHit'] * .8) * R)
	if A['snareHit']: add_pulse(W * random.uniform(.1, .9), H * random.uniform(.15, .85), (.5 + A['snareHit'] * .6) * R)
	if not on:
		S['idle'] -= dt
		if S['idle'] <= 0: add_pulse(W * random.uniform(.2, .8), H * random.uniform(.2, .8), .7); S['idle'] = random.uniform(1.5, 3.)
	for p in S['pulses']: p[2] += dt
	S['pulses'] = [p for p in S['pulses'] if p[2] < 4]
	gt = (.5 - A['busy'] * .22) if on else .5
	S['gate'] += (gt - S['gate']) * (1 - math.exp(-dt * 1.5))
	S['hue'] += dt * (.01 + A['centroid'] * .03)
	setv(g, 0, (S['t'], P('Hrows'), P('Hbright') * (1 + A['kickEnv'] * .25 * R), S['gate']))
	setv(g, 1, (1.1 + (b['kick'] * .5 + A['energy'] * .3) * R if on else 1.1, H * .35, S['hue'], 1.0 if P('Colour') else 0.0))
	for i in range(8):
		setv(g, 2 + i, S['pulses'][i] if i < len(S['pulses']) else (0, 0, 0, 0))
