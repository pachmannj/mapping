# SCÉNA KVĚT — skutečná lilie z časosběru (Mixkit 34700): 64 fází rozkvětu je v Texture 3D, hudba volí fázi.
# Vnitřní režisér střídá looky (klid = reál, plná hudba a dropy = netradiční):
#   real     celá lilie: v tichu se zavře do pupenu, s energií rozkvete, kopák ji „nadechne“
#   rings    spektrální kruhy: každý prstenec od středu je v jiné fázi rozkvětu podle svého pásma
#   slices   kubistické výseče: úhlové výseče květu, každá v čase podle svého pásma
#   echo     ozvěna: několik fází rozkvětu přes sebe, barevně posunuté
#   mandala  lilie zrcadlená do mandaly, zrcadla se točí s energií
import math, random

SHOW = '/project1/show'
Fc = '/project1/show/flower'
FRAMES = 64
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

def preload():
	"""jednou po startu: nahraje 64 fází rozkvětu do Texture 3D (4 snímky na fázi, ~4 s, scéna nemusí být aktivní).
	Průběžné nahrávání Texture 3D musí být vypnuté (Active = off), jinak přepisuje vrstvy od začátku."""
	if S.get('loaded'): return
	S['loaded'] = True
	src, t = f('frame_src'), f('phases')
	t.par.active = False; t.par.resetpulse.pulse()
	for k in range(FRAMES):
		run("op(%r).par.file = %r" % (src.path, 'media/lily/f_%02d.jpg' % (k + 1)), delayFrames=4 * k + 2)
		run("t = op(%r); t.par.replaceindex = %d; t.par.replacesinglepulse.pulse(); t.cook(force=True)" % (t.path, k), delayFrames=4 * k + 5)

LOOKS = {
	'real':    dict(rings=0.0, slices=0.0, echo=0.0, fold=0.0, hue=0.0),
	'rings':   dict(rings=1.0, slices=0.0, echo=0.0, fold=0.0, hue=.25),
	'slices':  dict(rings=.2, slices=1.0, echo=0.0, fold=0.0, hue=.45),
	'echo':    dict(rings=.3, slices=0.0, echo=1.0, fold=0.0, hue=.3),
	'mandala': dict(rings=.6, slices=0.0, echo=.4, fold=1.0, hue=.55),
}
CALM, WILD = ['real', 'echo'], ['rings', 'slices', 'mandala']

def direct(A, dt, now, on, B):
	man = P('Flook')
	if man != 'auto': S['look'] = man; return
	S['avgB'] += (B - S['avgB']) * min(1.0, dt / 8)
	S['lookT'] += dt
	ab = P('Fabstract')
	def pick(wild):
		pool = [l for l in (WILD if wild else CALM) if l != S['look']] or (WILD if wild else CALM)
		S['look'] = random.choice(pool); S['lookBeat'] = S['beats']; S['lookT'] = 0.0
	if on:
		if B - S['avgB'] > .2 and B > .55 and now - S['lastDrop'] > 15:
			S['lastDrop'] = now; pick(random.random() < .4 + ab * .6)
		elif S['beats'] - S['lookBeat'] >= 32 or (S['lookT'] > 25 and S['beats'] - S['lookBeat'] < 2):
			pick(random.random() < ab * (.25 + B * .75))
		elif B < .2 and S['look'] in WILD and S['lookT'] > 4:
			pick(False)
	elif S['lookT'] > 14:
		pick(random.random() < ab * .5)

def update(A, dt, now):
	if 'look' not in S:
		S.update(dict(t=0.0, bloom=.2, wave=9.0, waveA=0.0, beats=0, look='real', lookBeat=0, lookT=0.0, avgB=0.0, lastDrop=-99.0,
			hue=0.0, rot=0.0, rotV=0.0, rotT=0.0, mir=0.0, W=dict(LOOKS['real'])))
	preload()
	on = A['on']; R = P('Reactivity'); b = A['bands']; B = A['busy'] if on else 0
	S['t'] += dt
	tempo = A['tempo'] if (on and A['bpm']) else 1
	if A['kickHit'] and on:
		S['beats'] += 1; S['wave'] = 0.0; S['waveA'] = (.15 + A['kickHit'] * .25) * R
	S['wave'] += dt * (1.2 + tempo * .8)
	S['waveA'] *= math.exp(-dt * 2.5)
	# rozkvět: ticho = pupen, energie a hutnost = rozvitá lilie, kopák ji „nadechne“
	tgt = (.15 + A['energy'] * .35 + B * .55 + A['kickEnv'] * .12) * P('Fbloom') if on else (.35 + .3 * math.sin(S['t'] * .25))
	S['bloom'] += (min(1.0, tgt) - S['bloom']) * (1 - math.exp(-dt * (3.0 if tgt > S['bloom'] else .8)))
	direct(A, dt, now, on, B)
	tl = LOOKS[S['look']]; W = S['W']; kf = 1 - math.exp(-dt * 1.4)
	for key, val in tl.items(): W[key] += (val - W[key]) * kf
	# natočení: tlumená pružina, virbl ho postrčí
	if A['snareHit'] and on: S['rotT'] = max(-.5, min(.5, S['rotT'] + random.choice((-1, 1)) * A['snareHit'] * .2 * R))
	S['rotT'] *= math.exp(-dt * .4)
	S['rotV'] += ((S['rotT'] - S['rot']) * 5.0 - S['rotV'] * 4.0) * dt
	S['rot'] += S['rotV'] * dt
	S['hue'] += dt * (.05 + (A['centroid'] * .2 + B * .2) * on)
	lob = A['LOB'] if on else [.4 + .25 * math.sin(S['t'] * .5 + i * .6) for i in range(12)]
	rend = f('lily'); asp = rend.width / max(1, rend.height)
	g = f('lily')
	setv(g, 0, (S['bloom'], W['rings'] * P('Fspread') * R, W['slices'] * P('Fspread') * R, W['echo']))
	setv(g, 1, (.5, .63, .32, 6 + 2 * round(B * 3)))
	setv(g, 2, (S['wave'], S['waveA'] * (1 + W['rings']), S['hue'] * 3, W['hue']))
	setv(g, 3, (P('Fzoom') * (1 + A['kickEnv'] * .03 * on), S['rot'], P('Fbright'), asp))
	setv(g, 4, tuple(lob[0:4])); setv(g, 5, tuple(lob[4:8])); setv(g, 6, tuple(lob[8:12]))
	# mandala: zrcadla kolem středu obrazu (lilie je vycentrovaná), točí se s energií
	S['mir'] = (S['mir'] + dt * (6 + (A['energy'] * 30 + B * 25) * R * on) * tempo) % 360.0
	setv(f('fold'), 0, (S['mir'] * .5, 60 + S['mir'], 120 - S['mir'] * .3, 0))
	setv(f('fold'), 1, (0, 3, asp, 0))
	f('fold_mix').par.cross = W['fold']
	f('fb_lvl').par.opacity = min(.9, .45 + B * .35 + W['echo'] * .1)

def look_name(): return S.get('look', '')
