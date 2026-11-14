# SCÉNA KYTICE — procedurální květiny z půl milionu svítících bodů (chryzantémy, pivoňky, lilie), kamera pomalu
# proplouvá kyticí s malou hloubkou ostrosti (rozmazané světelné skvrny vpředu i vzadu). Body počítá shader
# bouquet_sim.glsl, takže květy skutečně rozkvétají. Reakce na hudbu:
#   energie + každá změna v hudbě → rozkvět (lilie se ohne dozadu, pivoňky se otevřou)
#   kopák → vlna po lístcích od středu ke špičkám, lilie blikne, kamera se nadechne dopředu
#   virbl → přeostření kamery na jinou květinu (rack focus)
#   hi-haty a výšky → chvění lístků · hutnost hudby → části květů se rozpadají do mlhy a zase skládají
import math, random

SHOW = '/project1/show'
Qc = '/project1/show/bouquet'
S = {}

# body, na které kamera ostří (středy květin v bouquet_sim.glsl)
FOCUS = [(x * 1.55, y * 1.15, z * 1.15) for x, y, z in ((.15, .55, .2), (-.55, .05, .35), (.75, -.15, -.15), (-.2, -.55, .55), (-.95, .65, -.5), (.55, -.85, .45))]

def P(name): return getattr(op(SHOW).par, name).eval()
def q(name): return op(Qc + '/' + name)

def num(x):
	# TD 2025.33230 převádí subnormální čísla (např. doznívající záblesk 5e-324) na 1.8e308 → bílý obraz; NaN/inf taky pryč
	x = float(x)
	return 0.0 if x != x or abs(x) < 1e-12 or abs(x) > 1e12 else x

def setv(o, i, v):
	p = o.par
	getattr(p, 'vec%dvaluex' % i).val, getattr(p, 'vec%dvaluey' % i).val = num(v[0]), num(v[1])
	getattr(p, 'vec%dvaluez' % i).val, getattr(p, 'vec%dvaluew' % i).val = num(v[2]), num(v[3])

def dev(key, x, dt, tau=4.0):
	"""odchylka od klouzavého průměru: reaguje na každou změnu v hudbě, ne na celkovou hlasitost"""
	m = S.setdefault('avg_' + key, x)
	S['avg_' + key] = m + (x - m) * min(1.0, dt / tau)
	return x - m

def update(A, dt, now):
	if 'bloom' not in S:
		S.update(dict(t=0.0, bloom=.4, wave=9.0, waveA=0.0, flash=0.0, mist=0.0, ang=0.0, push=0.0, pushV=0.0,
			fi=0, focus=3.4, fl=0.0))
	on = A['on']; R = P('Reactivity'); B = A['busy'] if on else 0; b = A['bands']; e = A['energy']
	S['t'] += dt
	tempo = A['tempo'] if (on and A['bpm']) else 1
	if A['kickHit'] and on:
		S['wave'] = 0.0; S['waveA'] = (.6 + A['kickHit'] * .9) * R * P('Qwave')
		S['flash'] = max(S['flash'], A['kickHit']); S['pushV'] += A['kickHit'] * .9 * R * P('Qcam')
	if A['snareHit'] and on and random.random() < .5:   # přeostření na jinou květinu
		S['fi'] = random.choice([i for i in range(len(FOCUS)) if i != S['fi']])
	S['wave'] += dt * (1.1 + tempo * .6)
	S['waveA'] *= math.exp(-dt * 1.8); S['flash'] *= math.exp(-dt * 4.0)
	# rozkvět
	tgt = ((.25 + e * .45 + B * .3 + dev('e', e, dt) * 1.4 + A['kickEnv'] * .12) * P('Qbloom')) if on else (.45 + .3 * math.sin(S['t'] * .2))
	tgt = max(.1, min(1.0, tgt))
	S['bloom'] += (tgt - S['bloom']) * (1 - math.exp(-dt * (6.0 if tgt > S['bloom'] else 1.5)))
	# rozpad do mlhy: hutnost + výšky, ale ne pořád
	mt = (B * .25 + max(0.0, dev('air', b['air'], dt, 3.0)) * 2.5 + A['hatEnv'] * .2) * on * P('Qmist')
	S['mist'] += (mt - S['mist']) * (1 - math.exp(-dt * (4.0 if mt > S['mist'] else 1.2)))
	flutter = (.3 + A['hatEnv'] * 1.5 + b['air'] * 1.0) * on * R + (.25 if not on else 0)
	g = q('sim')
	setv(g, 0, (S['t'], S['bloom'], A['kickEnv'] * on * R, flutter))
	setv(g, 1, (S['wave'], S['waveA'], S['mist'], P('Qbright')))
	setv(g, 2, (0, S['flash'] * R, P('Qcolor'), 0))
	lob = A['LOB'] if on else [.4 + .2 * math.sin(S['t'] * .5 + i) for i in range(12)]
	for i in range(3): setv(g, 3 + i, tuple(lob[4 * i:4 * i + 4]))
	# kamera: pomalý oblet kytice, s energií rychlejší; kopák ji nadechne dopředu (pružina)
	S['ang'] += dt * (.08 + (e * .12 + B * .08) * on) * tempo * P('Qcam')
	S['pushV'] += (-S['push'] * 10.0 - S['pushV'] * 4.0) * dt; S['push'] += S['pushV'] * dt
	a = math.sin(S['ang']) * .85                       # kamera se kývá ±50° před kyticí (zezadu květy nejsou vidět)
	rad = 3.7 - S['push'] * .4 + .45 * math.sin(a * .7)
	cx, cy, cz = math.sin(a) * rad * .8, .7 + .35 * math.sin(S['ang'] * .45), math.cos(a) * rad
	c = q('cam'); tx, ty, tz = 0.0, .05, .05
	c.par.tx, c.par.ty, c.par.tz = cx, cy, cz
	dx, dy, dz = tx - cx, ty - cy, tz - cz
	# natočení řeší Look At na null „target“
	# ostření: plynule na vybranou květinu
	fx, fy, fz = FOCUS[S['fi']]
	fd = math.sqrt((fx - cx) ** 2 + (fy - cy) ** 2 + (fz - cz) ** 2)
	S['focus'] += (fd - S['focus']) * (1 - math.exp(-dt * 2.5))
	r = q('render')
	setv(q('mat'), 0, (P('Qsize'), r.width, r.height, 0))
	setv(q('mat'), 1, (S['focus'], 26 * P('Qdof'), 11 * P('Qdof') + .01, 0))

def look_name(): return 'kytice'
