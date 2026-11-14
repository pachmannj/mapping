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
	F['spin'] += dt * (.12 + (inten * .5 + x['surge'] * .8) * on) * (x['bpm'] / 120.0) * P('Fspin')
	return ORDER[F['i']], ORDER[F['j']], F['m'] if F['morph'] else 0.0, F['spin'], 1.45

def update(A, dt, now):
	op(SHOW + '/sc_bouquet').module.run(A, dt, now, PATH, S, species)

def look_name():
	F = S.get('F')
	return NAMES.get(ORDER[F['i']], '') if F else ''
