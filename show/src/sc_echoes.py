# SCÉNA ECHOES — tečkový rastr (port z echoes_index.html)
# kopák = vlna ze středu, virbl = vlna z náhodného místa, basa = vlnění kolem bloudícího bodu, výšky = rychlost šumu
import math, random

SHOW = '/project1/show'
G = '/project1/show/echoes/glsl'
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
	if not S: S.update(dict(t=0.0, wt=0.0, hue=random.random(), pulses=[], idle=0.0, gate=.3, bright=1.0))
	on = A['on']; R = P('Reactivity'); b = A['bands']
	S['t'] += dt * (.6 + (b['air'] * 1.2 + A['hatEnv'] * .8) * R if on else .5)
	S['wt'] += dt
	if A['kickHit']: add_pulse(W * .5, H * .5, (.5 + A['kickHit'] * .7) * R)
	if A['snareHit']: add_pulse(W * random.uniform(.15, .85), H * random.uniform(.2, .8), (.4 + A['snareHit'] * .5) * R)
	if not on:                                              # bez zvuku občas samo „kápne“
		S['idle'] -= dt
		if S['idle'] <= 0: add_pulse(W * random.uniform(.2, .8), H * random.uniform(.2, .8), .6); S['idle'] = random.uniform(1.5, 3.5)
	for p in S['pulses']: p[2] += dt
	S['pulses'] = [p for p in S['pulses'] if p[2] < 5]
	t = S['wt']
	mx = W * (.5 + .32 * math.sin(t * .23) + .1 * math.sin(t * .71)); my = H * (.5 + .3 * math.cos(t * .19))
	wave = (b['sub'] * .4 + b['kick'] * .3) * R if on else .25
	gt = (.42 - A['busy'] * .2) if on else .45                # tiché pasáže = méně teček, plné = víc
	S['gate'] += (gt - S['gate']) * (1 - math.exp(-dt * 1.5))
	S['hue'] += dt * (.01 + A['centroid'] * .03)
	setv(g, 0, (S['t'], P('Espacing'), P('Ebright') * (1 + A['kickEnv'] * .3 * R), S['gate']))
	setv(g, 1, (mx, my, wave, t))
	setv(g, 2, (S['hue'], 1.0 if P('Colour') else 0.0, 1.2 + A['energy'] * .4, 0))
	for i in range(8):
		setv(g, 3 + i, S['pulses'][i] if i < len(S['pulses']) else (0, 0, 0, 0))
