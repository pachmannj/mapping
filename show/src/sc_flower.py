# SCÉNA KVĚT — jedna velká květina ze svítících bodů ve stejném nastavení jako Kytice (znaky / body, rytmus, rány, kamera
# létá okolo; posuvníky v záložce Kytice platí i tady). Teď jen lilie; když do ORDER přidáš další druhy, květina se
# podle beatu a písničky pořád dokola proměňuje v další druhy. Body přeletí obloukem z lístků jednoho
# druhu do lístků druhého. Čím víc se písnička rozjede, tím častěji se druh mění (každé 2 takty až každé 2 doby),
# drop přepne hned. Květ se přitom pomalu otáčí kolem své osy, s tempem rychleji.
import math

SHOW = '/project1/show'
PATH = '/project1/show/flower'
S = {}
ORDER = [2]                         # jen lilie (další druhy v bouquet_sim.glsl: 0 chryzantéma, 1 pivoňka, 3 tulipán, 4 kopretina, 5 růže)
NAMES = {0: 'chryzantéma', 1: 'pivoňka', 2: 'lilie', 3: 'tulipán', 4: 'kopretina', 5: 'růže'}

def P(name): return getattr(op(SHOW).par, name).eval()

def species(St, A, dt, now, x):
	"""vybere druh: přepíná na doby (víc energie = častěji), drop hned; vrací (druh A, druh B, morf, otočení, velikost)"""
	F = St.setdefault('F', dict(i=0, j=0, m=0.0, morph=False, last=0.0, spin=0.0, drop=0.0))
	on, bp, inten = x['on'], x['bp'], x['inten']
	# kolik dob mezi přepnutími: klid 8, rozjetá písnička 4 → 2 (posuvník Rychlost přepínání to násobí)
	every = 8.0 if inten < .35 else (4.0 if inten < .7 else 2.0)
	every = max(1.0, every / max(.25, P('Fswitch')))
	if not on: every = 6.0
	beat_s = 60.0 / max(60.0, x['bpm'])
	drop = x['surge'] > .5 and now - F['drop'] > 4
	if len(ORDER) > 1 and not F['morph'] and (bp - F['last'] >= every or drop):
		if drop: F['drop'] = now
		F['last'] = math.floor(bp + .5)                  # přepínat na celé doby
		F['j'] = (F['i'] + 1) % len(ORDER); F['morph'] = True; F['m'] = 0.0
	if F['morph']:
		dur = max(.35, min(1.4, beat_s * (1.5 if every <= 2 else 2.5)))   # proměna trvá 1,5–2,5 doby
		F['m'] += dt / dur
		if F['m'] >= 1.0: F['i'] = F['j']; F['m'] = 0.0; F['morph'] = False
	def lp(key, v, up, down):
		o = F.setdefault(key, v); F[key] = o + (v - o) * (1 - math.exp(-dt * (up if v > o else down))); return F[key]
	# DLOUHÝ TÓN / ZPĚV: dokud tón drží (stálé hlasité středy), květ se nafukuje a kolem něj houstne atmosféra;
	# čím déle tón trvá, tím víc (plno za ~3 s); když skončí, pomalu se stáhne zpátky
	# tón = hlasité středy (zpěv, synťák, pad), které se málo mění; měří se na vlastním vyhlazení pásem 4–8
	L = A['LOB']; mid = sum(L[4:9]) / 5.0
	mS = lp('midS', mid, 6.0, 6.0)
	chg = abs(mid - F.get('midP', mid)) / max(dt, 1e-3); F['midP'] = mid
	steady = max(0.0, 1.0 - lp('chg', chg, 4.0, 4.0) * 1.2)
	tone = lp('tone', mS * steady, 3.0, 3.0) * on
	# práh se přizpůsobí písničce: tón nad ~90 % dlouhodobého průměru nafukuje, pod ním květ splaskne
	avg = lp('toneAvg', tone, .05, .05)
	F['hold'] = min(6.0, max(0.0, F.get('hold', 0.0) + dt * max(-1.5, min(1.0, (tone - avg * .9) * 10.0))))
	infl = lp('infl', min(1.0, F['hold'] / 3.0) * P('Finflate'), .7, .35)
	# ROZJEZD: když se písnička rychle rozjede, květ se točí rychleji a zvětší se
	ramp = lp('ramp', min(1.0, inten * .6 + x['surge'] * .9) * on, .8, .3)
	rate = (.08 + ramp * .9) * (x['bpm'] / 120.0) * P('Fspin')
	F['spinV'] = lp('spinV', rate, 1.0, .5)
	F['spin'] += dt * F['spinV']
	# NAKLÁNĚNÍ V RYTMU jako ve větru: kolébání tam a zpět po taktech (síla podle rytmu), k tomu poryvy
	lean = math.sin(bp * math.pi / 4) * (.12 + x['kR'] * .22) + math.sin(F['spin'] * .37 + bp * .21) * .06
	tilt = lp('tilt', lean * P('Flean'), 2.0, 2.0)
	size = 1.1 * (1 + infl * .35 + ramp * .22)
	return ORDER[F['i']], ORDER[F['j']], F['m'] if F['morph'] else 0.0, F['spin'], (size, infl, tilt)

def update(A, dt, now):
	op(SHOW + '/sc_bouquet').module.run(A, dt, now, PATH, S, species)

def look_name():
	F = S.get('F')
	return NAMES.get(ORDER[F['i']], '') if F else ''
