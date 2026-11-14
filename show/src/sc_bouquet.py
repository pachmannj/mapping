# SCÉNA KYTICE — procedurální květiny z půl milionu svítících bodů (chryzantémy, pivoňky, lilie), kamera pomalu
# proplouvá kyticí s malou hloubkou ostrosti (rozmazané světelné skvrny vpředu i vzadu). Body počítá shader
# bouquet_sim.glsl, takže květy skutečně rozkvétají. Reakce na hudbu:
#   energie + každá změna v hudbě → rozkvět (lilie se ohne dozadu, pivoňky se otevřou)
#   každá květina poslouchá své pásmo (rozkvět, vlnění lístků, záře); vítr ohýbá stonky, po lístcích běží vlny
#   kopák → měkká vlna po lístcích, lilie se rozzáří, kamera se plynule nadechne dopředu
#   virbl → přeostření kamery na jinou květinu (rack focus)
#   hi-haty a výšky → chvění lístků · hutnost hudby → části květů se rozpadají do mlhy a zase skládají
import math, random

SHOW = '/project1/show'
Qc = '/project1/show/bouquet'
S = {}

# body, na které kamera ostří = středy květin v bouquet_sim.glsl (FOCUS níže)

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

def lp(key, x, dt, up=3.0, down=None):
	"""plynulé sledování hodnoty (náběh / doběh za sekundu) — nic neskočí"""
	v = S.setdefault(key, x)
	r = up if x > v else (down if down is not None else up)
	S[key] = v + (x - v) * (1 - math.exp(-dt * r))
	return S[key]

FOCUS = [(x * 1.55, y * 1.15, z * 1.15) for x, y, z in ((.15, .55, .2), (-.78, .42, -.2), (.88, .22, .2), (-.05, -.42, .62), (-.5, -.1, .3), (.72, -.42, -.15))]

def update(A, dt, now):
	if 'bloom' not in S:
		S.update(dict(t=0.0, ph=0.0, bloom=.4, wave=9.0, waveA=0.0, kick=0.0, ang=0.0, fi=0, focus=3.4, lastFocus=0.0,
			lobS=[.4] * 12, lobL=[.4] * 12, lobO=[.4] * 12))
	on = A['on']; R = P('Reactivity'); B = A['busy'] if on else 0; b = A['bands']; e = A['energy']
	S['t'] += dt
	tempo = A['tempo'] if (on and A['bpm']) else 1
	eS = lp('eS', e * on, dt, 2.5, 1.0); bS = lp('bS', B, dt, 1.5, .6)
	# ROZJEZD písničky: dlouhodobý průměr energie vs. teď. Když hudba naroste (build-up) → intenzita roste plynule,
	# když přijde drop (skok energie po tišší pasáži) → „vlna“ surge, která celou kytici rozpohybuje a rozbarví a pomalu doznívá.
	eL = lp('eL', eS, dt, 1 / 10.0)
	rise = max(0.0, eS - eL)
	inten = lp('inten', max(0.0, min(1.0, eS * .55 + bS * .45 + rise * 2.5)) * on, dt, 1.5, .4)
	if on and rise > .14 and eS > .45 and now - S.get('lastDrop', -99) > 8:
		S['lastDrop'] = now; S['surgeT'] = 1.0
	S['surgeT'] = S.get('surgeT', 0.0) * math.exp(-dt / 5.0)
	surge = lp('surge', S['surgeT'], dt, 2.5, 3.0)
	# hudební čas: rychlost proudění roste s energií, hutností a rozjezdem, ale fáze se jen plynule sčítá → žádné trhnutí
	speed = lp('spd', (.3 + eS * 1.0 + bS * .7 + inten * .8 + surge * 1.6) * (tempo if on else 1) + (0 if on else .15), dt, 1.2, .6)
	S['ph'] += dt * speed
	# kopák: měkká vlna po lístcích (náběh vyhlazený)
	if A['kickHit'] and on and S['wave'] > .5:
		S['wave'] = 0.0; S['kick'] = (.5 + A['kickHit'] * .6) * R * P('Qwave')
	S['wave'] += dt * (.9 + tempo * .4)
	S['kick'] *= math.exp(-dt * 1.5)
	waveA = lp('waveA', S['kick'], dt, 9.0, 3.0)
	# pásma: rychlé vyhlazení + pomalý průměr → každá květina reaguje na změny ve svém pásmu, ne na hlasitost
	lob = A['LOB'] if on else [.4 + .2 * math.sin(S['t'] * .5 + i) for i in range(12)]
	fa, fs = 1 - math.exp(-dt * 4.0), 1 - math.exp(-dt / 6.0)
	out = []
	for i in range(12):
		S['lobS'][i] += (lob[i] - S['lobS'][i]) * fa
		S['lobL'][i] += (lob[i] - S['lobL'][i]) * fs
		v = max(0.0, min(1.0, .3 + S['lobS'][i] * .45 + (S['lobS'][i] - S['lobL'][i]) * 1.8 * R))
		S['lobO'][i] += (v - S['lobO'][i]) * (1 - math.exp(-dt * 2.5))
		out.append(S['lobO'][i])
	# rozkvět (společný základ, každá květina k tomu přidá své pásmo)
	tgt = ((.22 + eS * .45 + bS * .25 + inten * .2 + surge * .3) * P('Qbloom')) if on else (.45 + .3 * math.sin(S['t'] * .2))
	bloom = lp('bloom', max(.1, min(1.0, tgt)), dt, 1.5, .7)
	mist = lp('mist', (bS * .25 + max(0.0, S['lobS'][11] - S['lobL'][11]) * 1.5 + surge * .6) * on * P('Qmist'), dt, 1.2, .5)
	flutter = lp('flut', (.25 + A['hatEnv'] * .8 + b['air'] * .6) * on * R + (.2 if not on else 0), dt, 2.0, 1.0)
	breathe = lp('brth', A['kickEnv'] * on * R, dt, 5.0, 2.0)
	wind = lp('wind', .3 + (eS * .6 + bS * .4 + inten * .6 + surge * 1.2) * R * on, dt, 1.0, .5)
	und = lp('und', .45 + (eS * .6 + bS * .4 + inten * .6 + surge * 1.0) * on, dt, 1.0, .5)
	glow = lp('glow', (A['kickEnv'] * .8 + surge * .6) * on * R, dt, 6.0, 2.0)
	# barvy lilií: odstín se posouvá rychlostí podle intenzity (v klidu skoro stojí), rozptyl mezi liliemi roste s rozjezdem
	S['hue'] = S.get('hue', 0.0) + dt * (.02 + (inten * .25 + surge * .9 + A['centroid'] * .1) * on * P('Qhue'))
	spread = lp('hsp', (.15 + inten * .25 + surge * .3) * on * P('Qhue') + .1, dt, 1.0, .4)
	g = q('sim')
	setv(g, 0, (S['t'], bloom, breathe, flutter))
	setv(g, 1, (S['wave'], waveA, mist, P('Qbright')))
	setv(g, 2, (math.sin(S['hue']) * .75, glow,   # odstín se kývá v rozsahu korálová ↔ růžová ↔ fialová (nikdy zelená)
		 P('Qcolor') * (.85 + inten * .25), spread))
	setv(g, 3, (S['ph'], wind, und, 0))
	for i in range(3): setv(g, 4 + i, tuple(out[4 * i:4 * i + 4]))
	# kamera: pomalé kývání před kyticí podle hudebního času, dopředu se nadechne vyhlazeně
	S['ang'] += dt * (.05 + (eS * .07 + bS * .05 + inten * .06 + surge * .22) * on) * P('Qcam')
	push = lp('push', (A['kickEnv'] * .15 * R + eS * .1 + surge * .25) * on * P('Qcam'), dt, 1.5, .6)
	a = math.sin(S['ang']) * .75                       # kamera se kývá ±45° před kyticí (zezadu květy nejsou vidět)
	rad = 4.5 - push + .35 * math.sin(S['ang'] * .7)
	cx, cy, cz = math.sin(a) * rad * .8, .7 + .3 * math.sin(S['ang'] * .45), math.cos(a) * rad
	c = q('cam')
	c.par.tx, c.par.ty, c.par.tz = cx, cy, cz          # natočení řeší Look At na null „target“
	# ostření: na virbl přeostří na jinou květinu, nejvýš jednou za 4 s, plynule
	if A['snareHit'] and on and now - S['lastFocus'] > 4:
		S['fi'] = random.choice([i for i in range(len(FOCUS)) if i != S['fi']]); S['lastFocus'] = now
	fx, fy, fz = FOCUS[S['fi']]
	fd = math.sqrt((fx - cx) ** 2 + (fy - cy) ** 2 + (fz - cz) ** 2)
	S['focus'] += (fd - S['focus']) * (1 - math.exp(-dt * 1.2))
	r = q('render')
	setv(q('mat'), 0, (P('Qsize'), r.width, r.height, 0))
	setv(q('mat'), 1, (S['focus'], 12 * P('Qdof') + .01, 5, 14))

def look_name(): return 'kytice'
