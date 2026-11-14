# SCÉNA KYTICE — procedurální květiny ze svítících bodů, převedené do znaků (ASCII / písmena) nebo jako body; kamera létá okolo
# proplouvá kyticí s malou hloubkou ostrosti (rozmazané světelné skvrny vpředu i vzadu). Body počítá shader
# bouquet_sim.glsl, takže květy skutečně rozkvétají. Reakce na hudbu:
#   energie + každá změna v hudbě → rozkvět (lilie se ohne dozadu, pivoňky se otevřou)
#   RYTMUS: hodiny svázané s tempem → lilie se otevírají na 1 a 3 (kopák), chryzantémy na 2 a 4 (virbl), pivoňky na osminy;
#   s každým úderem proběhne vlna lístky, kytice se kolébá v taktu, kamera se na dobu nadechne
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

def motion(St, A, dt, x, pfx):
	"""plavání jako Vortex (Květ i Kytice): nafouknutí dlouhým tónem / zpěvem, rozjezd, náklon v rytmu jako ve větru, otáčení.
	pfx = předpona parametrů ('F' Květ, 'Q' Kytice): …inflate, …lean, …spin. Vrací (nafouknutí, rozjezd, náklon, otočení)."""
	M = St.setdefault('M', dict(spin=0.0))
	on, bp, dt_ = x['on'], x['bp'], max(dt, 1e-3)
	def lp_(key, v, up, down):
		o = M.setdefault(key, v); M[key] = o + (v - o) * (1 - math.exp(-dt * (up if v > o else down))); return M[key]
	# DLOUHÝ TÓN / ZPĚV: hlasité středy (zpěv, synťák, pad), které se málo mění; dokud tón drží, nafukuje se (plno za ~3 s),
	# když skončí, pomalu se stáhne. Práh se přizpůsobí písničce (tón musí vyčnívat nad dlouhodobý průměr).
	L = A['LOB']; mid = sum(L[4:9]) / 5.0
	mS = lp_('midS', mid, 6.0, 6.0)
	chg = abs(mid - M.get('midP', mid)) / dt_; M['midP'] = mid
	steady = max(0.0, 1.0 - lp_('chg', chg, 4.0, 4.0) * 1.2)
	tone = lp_('tone', mS * steady, 3.0, 3.0) * on
	avg = lp_('toneAvg', tone, .05, .05)
	M['hold'] = min(4.0, max(0.0, M.get('hold', 0.0) + dt * max(-2.0, min(1.0, (tone - avg * 1.08) * 10.0))))   # tón musí vyčnívat nad průměr
	infl = lp_('infl', min(1.0, M['hold'] / 3.0) * P(pfx + 'inflate'), .7, .35)
	# ROZJEZD: písnička se rychle rozjede → točí se rychleji a zvětší se
	ramp = lp_('ramp', min(1.0, x['inten'] * .6 + x['surge'] * .9) * on, .8, .3)
	M['spinV'] = lp_('spinV', (.08 + ramp * .9) * (x['bpm'] / 120.0) * P(pfx + 'spin'), 1.0, .5)
	M['spin'] += dt * M['spinV']
	# NÁKLON V RYTMU jako ve větru: kolébání po taktech (síla podle rytmu) + poryvy
	lean = math.sin(bp * math.pi / 4) * (.12 + x['kR'] * .22) + math.sin(M['spin'] * .37 + bp * .21) * .06
	tilt = lp_('tilt', lean * P(pfx + 'lean'), 2.0, 2.0)
	return infl, ramp, tilt, M['spin']

FOCUS = [(x * 1.55, y * 1.15, z * 1.15) for x, y, z in ((.15, .55, .2), (-.78, .42, -.2), (.88, .22, .2), (-.05, -.42, .62), (-.5, -.1, .3), (.72, -.42, -.15))]

def update(A, dt, now): run(A, dt, now, '/project1/show/bouquet', S)

def run(A, dt, now, path, state, solo=None):
	"""společné ovládání pro Kytici i Květ (sc_flower.py volá run se svou sítí, stavem a funkcí solo, která vybírá druh květu)"""
	global S, Qc
	keep = (S, Qc)
	S, Qc = state, path
	try: _update(A, dt, now, solo)
	finally: S, Qc = keep

def _update(A, dt, now, solo):
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
	speed = lp('spd', (.15 + eS * .35 + bS * .2 + inten * .25 + surge * .6) * (tempo if on else 1) + (0 if on else .15), dt, 1.2, .6)
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
	# ── RYTMICKÉ HODINY: fáze dob běží plynule podle tempa a každý kopák ji jemně doladí (bez skoku) ──
	bpm = A['bpm'] if (on and A['bpm']) else 100.0
	bpm = lp('bpmS', bpm, dt, .8)
	S['bp'] = S.get('bp', 0.0) + dt * bpm / 60.0
	if A['kickHit'] and on:
		frac = S['bp'] - math.floor(S['bp'])
		err = -frac if frac < .5 else 1.0 - frac        # ke kterému úderu je kopák nejblíž
		S['corr'] = err * .6                         # doladění jen částečně a pomalu → mávání nikdy necukne
		S['kstr'] = S.get('kstr', 0.0) + (min(1.0, .45 + A['kickHit'] * .7) - S.get('kstr', 0.0)) * .4
	if A['snareHit'] and on: S['sstr'] = S.get('sstr', 0.0) + (min(1.0, .45 + A['snareHit'] * .7) - S.get('sstr', 0.0)) * .4
	c_ = S.get('corr', 0.0) * min(1.0, dt * 1.8); S['bp'] += c_; S['corr'] = S.get('corr', 0.0) - c_
	# síla rytmu: bez kopáků (break, ticho) pulz během ~3 s vyprchá a kytice jen pluje; hi-haty = průměr jejich obálky
	S['kstr'] = S.get('kstr', 0.0) * math.exp(-dt / 3.0); S['sstr'] = S.get('sstr', 0.0) * math.exp(-dt / 3.0)
	hstr = lp('hstr', min(1.0, A['hatEnv'] * 1.5) * on, dt, 3.0, .5)
	kR = lp('kR', min(1.0, S['kstr'] * (.7 + inten * .5 + surge * .4)) * R, dt, 2.0, 1.0)
	sR = lp('sR', min(1.0, S['sstr'] * (.7 + inten * .5)) * R, dt, 2.0, 1.0)
	if not on: kR, sR, hstr = .25, .15, .1               # bez hudby jemné dýchání ve 100 BPM
	bar = S['bp'] % 4.0
	# ── RÁNY: každý kopák / virbl vyšle vlnu, která se šíří kytici; každá květina mávne, až k ní dorazí ──
	#    kopák = velké mávnutí zespodu, virbl = menší shora (střídavě zleva / zprava); pamatují se poslední 4 rány
	H = S.setdefault('hitq', [])
	#    klidněji: kopák vyšle vlnu nejvýš jednou za 2 doby (silný kopák dřív), virbl jen silný a nejvýš jednou za 4 doby
	beat_s = 60.0 / max(60.0, bpm)
	if on and A['kickHit'] and (S['t'] - S.get('lastK', -9) > 1.8 * beat_s or (A['kickHit'] > .95 and S['t'] - S.get('lastK', -9) > .9 * beat_s)):
		S['lastK'] = S['t']
		H.insert(0, [S['t'], min(1.3, .6 + A['kickHit'] * .8) * R * (1 + surge * .3) * .55, 0.0, -1.3])
	if on and A['snareHit'] > .55 and S['t'] - S.get('lastS', -9) > 3.6 * beat_s:
		S['lastS'] = S['t']
		side = 1.0 if S.get('sside', 1) > 0 else -1.0; S['sside'] = -side
		H.insert(0, [S['t'], min(.8, .3 + A['snareHit'] * .5) * R * .5, side * 1.2, 1.4])
	del H[4:]
	g = q('sim')
	setv(g, 0, (S['t'], bloom, breathe, flutter))
	setv(g, 1, (0, P('Qwave'), mist, P('Qbright')))
	setv(g, 2, (math.sin(S['hue']) * .75, glow,   # odstín se kývá v rozsahu korálová ↔ růžová ↔ fialová (nikdy zelená)
		 P('Qcolor') * (.85 + inten * .25), spread))
	setv(g, 3, (S['ph'], wind, und, 0))
	for i in range(3): setv(g, 4 + i, tuple(out[4 * i:4 * i + 4]))
	setv(g, 7, (bar, kR, sR, hstr * R))
	for i in range(4):
		h = H[i] if i < len(H) else [-99.0, 0.0, 0.0, 0.0]
		setv(g, 8 + i, (S['t'] - h[0], h[1], h[2], h[3]))
	# délka mávnutí podle tempa (~1 doba), rychlost šíření vlny kyticí roste s tempem
	flapT = min(1.8, max(.8, 2.0 * 60.0 / max(60.0, bpm))) * 1.6   # mávnutí delší a měkčí (plave jako Vortex)
	setv(g, 12, (flapT, 1.3 * (bpm / 120.0), S['bp'], 0))   # mávnutí ~2 doby, vlna pomalu
	# KVĚT (jedna květina): druh A → B, morf, otočení, velikost — vybírá sc_flower.py podle beatu a písničky
	if solo:
		ta, tb, m, spin, (size, infl, tilt) = solo(S, A, dt, now, dict(on=on, bp=S['bp'], bpm=bpm, inten=inten, surge=surge, kR=kR))
		setv(g, 13, (1, ta, tb, m)); setv(g, 14, (spin, size, infl, tilt))
	else:
		infl, ramp, tilt, spin = motion(S, A, dt, dict(on=on, bp=S['bp'], bpm=bpm, inten=inten, surge=surge, kR=kR), 'Q')
		setv(g, 13, (0, 0, 0, 0)); setv(g, 14, (spin * .15, 1 + infl * .07 + ramp * .06, infl * .5, tilt * .6))   # kytice se otáčí pomaleji
	# kamera: LÉTÁ OKOLO KYTICE, rychlost svázaná s tempem (1 oběh za 8 taktů = 32 dob), rozjezd a drop ji zrychlí;
	# výška se vlní po 2 taktech, vzdálenost dýchá, na každou dobu se kamera nadechne dopředu
	beat_s = 60.0 / max(60.0, bpm)
	orbit = lp('orb', (2 * math.pi / (64 * beat_s)) * (.6 + inten * .4 + surge * .6) if on else .06, dt, .6, .4)   # 1 oběh za 16 taktů
	S['ang'] += dt * orbit * P('Qcam')
	push = lp('push', (eS * .15 + surge * .4) * on * P('Qcam'), dt, 1.5, .6)
	bx = S['bp'] % 1.0
	a = math.sin(S['ang']) * .35 if solo else S['ang']   # Květ: kamera zůstává zepředu, jen se mírně kolébá (zboku květ není hezký)
	rad = (4.8 if solo else 4.7) - push + .5 * math.sin(S['bp'] * math.pi / 16)  # přiblížení a oddálení po 8 dobách
	cx, cy, cz = math.sin(a) * rad, (.25 if solo else .7) + (.25 if solo else .6) * math.sin(S['bp'] * math.pi / 8), math.cos(a) * rad
	c = q('cam')
	c.par.tx, c.par.ty, c.par.tz = cx, cy, cz          # natočení řeší Look At na null „target“
	# ostření: na virbl přeostří na jinou květinu, nejvýš jednou za 4 s, plynule
	if A['snareHit'] and on and now - S['lastFocus'] > 4:
		S['fi'] = random.choice([i for i in range(len(FOCUS)) if i != S['fi']]); S['lastFocus'] = now
	fx, fy, fz = (0.0, 0.0, 0.0) if solo else FOCUS[S['fi']]
	fd = math.sqrt((fx - cx) ** 2 + (fy - cy) ** 2 + (fz - cz) ** 2)
	S['focus'] += (fd - S['focus']) * (1 - math.exp(-dt * 1.2))
	# znaky: styl, velikost buňky (s hutností o kousek menší = jemnější), zamíchání znaků na dobu
	sty = {'points': 0, 'ascii': 1, 'letters': 2}.get(P('Qstyle'), 1)
	scr = (math.exp(-bx * 4.0) * min(1.0, bx / .05)) * (kR * .2 + sR * .1) + surge * .15
	# VELIKOST ZNAKŮ = JEN HLASITOST: čím hlasitější zvuk, tím větší znaky (okamžitý náběh, rychlý doběh → žádné zpoždění)
	loud = lp('loud', A['energy'] * on, dt, 30.0, 4.0)
	cell = 6.0 + loud * 14.0 * P('Qcellbeat')
	setv(q('ascii'), 0, (cell * P('Qcell') / 9.0, sty, 2.1, 0))   # pod znaky už nejsou vidět původní body
	setv(q('ascii'), 1, (S['t'], 0, P('Qcolor'), 0))   # znaky se nemíchají (plynulost)
	r = q('render')
	setv(q('mat'), 0, (P('Qsize'), r.width, r.height, 0))
	setv(q('mat'), 1, (S['focus'], 12 * P('Qdof') + .01, 5, 14))

def look_name(): return 'kytice'
