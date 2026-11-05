# SCÉNA ECHOES 2.0 — bílé linky z pole ozvěn: Edge ×5 → feedback → Limit (pixelace) → Displace → Edge → feedback se zoomem
# (podle Daniel Steenhoff „Realtime White Visuals“). Z webu zůstává logika: kopák = ozvěna ze středu,
# virbl = ozvěna z náhodného místa, basa = vlnění kolem bloudícího bodu, výšky = rychlost šumu.
import math, random

SHOW = '/project1/show'
E = '/project1/show/echoes'
S = {}

def P(name): return getattr(op(SHOW).par, name).eval()
def e(name): return op(E + '/' + name)

def num(x):
	# TD 2025.33230 převádí subnormální čísla (např. doznívající záblesk 5e-324) na 1.8e308 → bílý obraz; NaN/inf taky pryč
	x = float(x)
	return 0.0 if x != x or abs(x) < 1e-12 or abs(x) > 1e12 else x

def setv(o, i, v):
	p = o.par
	getattr(p, 'vec%dvaluex' % i).val, getattr(p, 'vec%dvaluey' % i).val = num(v[0]), num(v[1])
	getattr(p, 'vec%dvaluez' % i).val, getattr(p, 'vec%dvaluew' % i).val = num(v[2]), num(v[3])

def add_ring(x, y, amp):
	S['rings'].append([x, y, 0.0, amp]); S['rings'] = S['rings'][-8:]

def update(A, dt, now):
	if not S: S.update(dict(t=0.0, tx=0.0, wt=0.0, rings=[], idle=0.0, rot=0.0, rotV=0.0, pix=0.0, zoom=0.0))
	on = A['on']; R = P('Reactivity'); b = A['bands']; B = A['busy'] if on else 0
	S['t'] += dt * (.1 + (b['air'] * .25 + A['hatEnv'] * .2) * R * on)        # z videa: tz = absTime/10, tx = absTime/100
	S['tx'] += dt * .01
	S['wt'] += dt
	if A['kickHit']: add_ring(0.0, 0.0, (.6 + A['kickHit'] * .6) * R); S['zoom'] = max(S['zoom'], A['kickHit'] * R)
	if A['snareHit']:
		add_ring(random.uniform(-.7, .7), random.uniform(-.4, .4), (.5 + A['snareHit'] * .5) * R)
		S['pix'] = max(S['pix'], A['snareHit'] * R)
		S['rotV'] += (1 if random.random() < .5 else -1) * A['snareHit'] * .6 * R
	if not on:
		S['idle'] -= dt
		if S['idle'] <= 0: add_ring(random.uniform(-.6, .6), random.uniform(-.35, .35), .7); S['idle'] = random.uniform(1.5, 3.5)
	for r in S['rings']: r[2] += dt
	S['rings'] = [r for r in S['rings'] if r[2] < 4]
	t = S['wt']
	mx = .5 + .32 * math.sin(t * .23) + .1 * math.sin(t * .71); my = .5 + .3 * math.cos(t * .19)
	g = e('field')
	setv(g, 0, (S['t'], 1.4, 4.5, 1.1))                                 # hladké pole: perioda jako ve videu
	setv(g, 1, (mx, my, (b['sub'] * .35 + b['kick'] * .25) * R * on, t))
	setv(g, 2, (S['tx'], 0, 0, 0))
	for i in range(8):
		setv(g, 3 + i, S['rings'][i] if i < len(S['rings']) else (0, 0, 0, 0))
	# pixelace: krok kvantizace vyskočí na virbl a dozní (z videa: Limit TOP → Quantize Position → Round)
	S['pix'] *= math.exp(-dt * 4)
	step = P('Epixel') * (1 + S['pix'] * 2.5 + B * .8)
	e('limit').par.quantpos = 'round' if step > .001 else 'off'
	e('limit').par.posstep = max(step, .001)
	d = P('Edisp') * (1 + (b['low'] * .6 + A['kickEnv'] * .8) * R * on)
	e('displace').par.displaceweightx = d; e('displace').par.displaceweighty = d
	# druhá ozvěna: zoom 0,99 z videa, kopák ji krátce „nadechne“, virbl pootočí
	S['zoom'] *= math.exp(-dt * 5)
	S['rotV'] *= math.exp(-dt * 2); S['rot'] += S['rotV'] * dt * 20
	xf = e('fb2_xf').par
	xf.sx = xf.sy = .99 - S['zoom'] * .02
	xf.rotate = S['rot'] * .15
	e('fb2_lvl').par.opacity = P('Etrails')
	e('fb1_lvl').par.brightness1 = .9
	e('out_lvl').par.brightness1 = P('Ebright') * (1 + A['kickEnv'] * .3 * R * on)
