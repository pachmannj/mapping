# SCÉNA KVĚT — generativní 3D květ (fylotaxe: lístky po zlatém úhlu), lístky vykreslené na GPU (src/glsl/flower_*.glsl)
#   energie a hutnost hudby → květ se rozvíjí (vnější kruhy první), v tichu pomalu „dýchá“
#   12 pásem → každý kruh lístků se otevírá a svítí se svým pásmem (vnější = basy, vnitřní = výšky)
#   kopák → vlna putuje od středu ven, lístky se v ní rozsvítí a nadechnou
#   virbl → květ se zkroutí (tlumená pružina), hihat → chvění špiček
import math, random

SHOW = '/project1/show'
Fc = '/project1/show/flower'
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

def update(A, dt, now):
	if not S: S.update(dict(t=0.0, bloom=.3, wave=9.0, waveA=0.0, tw=0.0, twV=0.0, twT=0.0, hue=random.random(), rot=0.0, cam=0.0))
	on = A['on']; R = P('Reactivity'); b = A['bands']; B = A['busy'] if on else 0
	S['t'] += dt
	tempo = A['tempo'] if (on and A['bpm']) else 1
	# rozkvět: s energií hudby, v tichu pomalé dýchání
	tgt = (.25 + A['energy'] * .45 + B * .55) * P('Fbloom') if on else (.45 + .25 * math.sin(S['t'] * .35)) * P('Fbloom')
	S['bloom'] += (tgt - S['bloom']) * (1 - math.exp(-dt * (2.0 if tgt > S['bloom'] else .7)))
	# kopák: vlna od středu ven
	if A['kickHit'] and on:
		S['wave'] = 0.0; S['waveA'] = (.5 + A['kickHit'] * .8) * R
	S['wave'] += dt * (1.4 + tempo * .6)
	S['waveA'] *= math.exp(-dt * 1.2)
	# virbl: zkroucení jako tlumená pružina (žádné cukání)
	if A['snareHit'] and on:
		S['twT'] = max(-1.2, min(1.2, S['twT'] + random.choice((-1, 1)) * A['snareHit'] * .5 * R))
	S['twT'] *= math.exp(-dt * .5)
	S['twV'] += ((S['twT'] - S['tw']) * 7.0 - S['twV'] * 5.0) * dt
	S['tw'] += S['twV'] * dt
	S['hue'] += dt * (.012 + (A['centroid'] * .04 + B * .03) * on)
	S['rot'] += dt * (.05 + (A['energy'] * .15 + B * .1) * on) * P('Fspin')
	lob = A['LOB'] if on else [.3 + .15 * math.sin(S['t'] * .6 + i * .7) for i in range(12)]
	for name, n, mode in (('mat_petals', int(P('Fpetals')), 0), ('mat_seeds', 500, 1)):
		m = f(name)
		setv(m, 0, (n, S['bloom'], P('Fsize'), S['t']))
		setv(m, 1, (S['wave'], S['waveA'], S['tw'], A['hatEnv'] * R * on))
		setv(m, 2, (S['hue'], .72, P('Fbright') * (.8 + A['energy'] * .3 * on), S['rot']))
		setv(m, 3, (P('Fcup'), 1.0, mode, 0))
		setv(m, 4, tuple(lob[0:4])); setv(m, 5, tuple(lob[4:8])); setv(m, 6, tuple(lob[8:12]))
	f('geo_petals').par.numinstances = int(P('Fpetals'))
	# kamera: květ je natočený ke kameře, pomalu se kolem něj krouží a kopák ji lehce přiblíží
	S['cam'] += dt * (.12 + B * .15)
	c = f('cam').par
	tilt = .35 + .2 * math.sin(S['cam'] * .7)
	d = 3.6 - A['kickEnv'] * .2 * on
	c.tx, c.ty, c.tz = math.sin(S['cam']) * math.sin(tilt) * d, math.cos(S['cam']) * math.sin(tilt) * d, math.cos(tilt) * d
	f('fb_lvl').par.opacity = min(.9, .55 + B * .3)
