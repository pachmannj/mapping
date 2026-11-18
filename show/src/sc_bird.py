# SCÉNA KŘÍDLA (místo Ptáka) — abstraktní pár křídel z peří v barvách termokamery, stíny se rozlévají do krajů,
# v pozadí skutečné hejno špačků z videa (Pexels 3851642, Egor Kunovsky), ptáci teplí, jejich stopy chladnou.
#   tempo   → mávání: jeden plynulý mávnutí nahoru a dolů za 2 doby (rychlá písnička = rychlé mávání)
#   energie → výška mávnutí a „teplo“ (rychle se pohybující části křídla se rozžhaví do žluta a bíla)
#   kopák   → krátké rozžhavení křídel; drop → velké mávnutí
#   hutnost → stíny se rozlévají dál; video hejna plyne rychleji s energií
#   pásma   → každé pero září podle svého pásma
import math

SHOW = '/project1/show'
Bd = '/project1/show/bird'
S = {}

def P(name): return getattr(op(SHOW).par, name).eval()
def k(name): return op(Bd + '/' + name)

def num(x):
	# TD 2025.33230 převádí subnormální čísla (např. doznívající záblesk 5e-324) na 1.8e308 → bílý obraz; NaN/inf taky pryč
	x = float(x)
	return 0.0 if x != x or abs(x) < 1e-12 or abs(x) > 1e12 else x

def setv(o, i, v):
	p = o.par
	getattr(p, 'vec%dvaluex' % i).val, getattr(p, 'vec%dvaluey' % i).val = num(v[0]), num(v[1])
	getattr(p, 'vec%dvaluez' % i).val, getattr(p, 'vec%dvaluew' % i).val = num(v[2]), num(v[3])

def lp(key, x, dt, up=3.0, down=None):
	"""plynulé sledování hodnoty (náběh / doběh za sekundu)"""
	v = S.setdefault(key, x)
	r = up if x > v else (down if down is not None else up)
	S[key] = v + (x - v) * (1 - math.exp(-dt * r))
	return S[key]

def update(A, dt, now):
	S.setdefault('t', 0.0); S.setdefault('fp', 0.0)
	on = A['on']; R = P('Reactivity'); B = A['busy'] if on else 0; e = A['energy']
	S['t'] += dt
	eS = lp('eS', e * on, dt, 3.0, 1.0); bS = lp('bS', B, dt, 1.5, .6)
	bpm = lp('bpm', A['bpm'] if (on and A['bpm']) else 90.0, dt, .8)
	# drop: energie vyskočí nad dlouhodobý průměr → velké mávnutí, které pomalu dozní
	eL = lp('eL', eS, dt, .1)
	if on and eS - eL > .14 and eS > .45 and now - S.get('lastDrop', -99) > 8: S['lastDrop'] = now; S['surgeT'] = 1.0
	S['surgeT'] = S.get('surgeT', 0.0) * math.exp(-dt / 4.0)
	surge = lp('surge', S['surgeT'], dt, 2.5, 2.0)
	# mávání: fáze běží plynule podle tempa (jeden mávnutí za 2 doby); každý kopák fázi jemně doladí na úder
	S['fp'] += dt * bpm / 60.0 / 2.0
	if on and A['kickHit']:
		fr = (S['fp'] * 2.0) % 1.0
		S['corr'] = (-fr if fr < .5 else 1.0 - fr) * .5 / 2.0
	c_ = S.get('corr', 0.0) * min(1.0, dt * 2.0); S['fp'] += c_; S['corr'] = S.get('corr', 0.0) - c_
	amp = lp('amp', (.35 + eS * .45 + surge * .4) * P('Bflap') * (R if on else .6), dt, 2.0, .8)
	ph = S['fp'] * 2 * math.pi
	ang = .18 + math.sin(ph) * amp                       # úhel křídla (nahoře + / dole −), plynulá sinusovka
	vel = math.cos(ph) * min(1.0, amp * 1.6)              # rychlost mávání (pro ohyb per a „teplo“)
	kick = lp('kick', A['kickEnv'] * on * R, dt, 20.0, 5.0)
	heat = (.5 + eS * .8 + surge * .6) * P('Bheat')
	w = k('wings')
	asp = w.width / max(1, w.height)
	setv(w, 0, (S['t'], ang, vel, heat))
	setv(w, 1, (asp, P('Bspan') * (1 + surge * .1), P('Babsorb') * .6, P('Bflock') * .28))
	setv(w, 2, (-.02 + math.sin(ph + .6) * .03 * amp, kick, math.sin(S['t'] * .05) * .5, P('Bbright')))
	lob = A['LOB'] if on else [.4] * 12
	for i in range(3): setv(w, 3 + i, tuple(lob[4 * i:4 * i + 4]))
	# stíny do krajů: s hutností se rozlévají dál a déle doznívají
	setv(k('spill'), 0, (min(.94, .84 + bS * .07 + surge * .03) if P('Bspill') > 0 else 0, .003 + (bS * .006 + eS * .004) * P('Bspill'), S['t'], asp))
	# hejno: video plyne rychleji s energií, stopy ptáků chladnou pomaleji s hutností
	k('video').par.speed = P('Bspeed') * (.6 + eS * .6 + surge * .4) if on else .5 * P('Bspeed')
	setv(k('flock'), 0, (min(.85, .65 + bS * .15), 1.0, 0, 0))

def look_name(): return 'křídla'
