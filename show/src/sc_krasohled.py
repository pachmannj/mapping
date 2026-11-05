# SCÉNA KRASOHLED 2.0 — zkroucený tunel z milionu bodů + kaskáda zrcadel (podle Acrylicode „Audio-reactive psychedelic visuals“)
# Z webové verze zůstává logika: laloky podle 12 pásem, morf počtu laloků po 8 úderech, rázová vlna na kopák,
# rotace od virblu. Nové: rotace zrcadel, která s hudbou roste do nekonečna, body proudí tunelem ke kameře.
import math, random, colorsys

SHOW = '/project1/show'
K = '/project1/show/krasohled'
S = {}
SEQ = [4, 6, 3, 8, 5, 4, 7, 12, 6, 4]
MIRRORS = (0., 90., 45., 180., 90.)                   # úhly zrcadel z videa; třetí se točí s hudbou

def P(name): return getattr(op(SHOW).par, name).eval()
def k(name): return op(K + '/' + name)

def num(x):
	# TD 2025.33230 převádí subnormální čísla (např. doznívající záblesk 5e-324) na 1.8e308 → bílý obraz; NaN/inf taky pryč
	x = float(x)
	return 0.0 if x != x or abs(x) < 1e-12 or abs(x) > 1e12 else x

def setv(o, i, v):
	p = o.par
	getattr(p, 'vec%dvaluex' % i).val, getattr(p, 'vec%dvaluey' % i).val = num(v[0]), num(v[1])
	getattr(p, 'vec%dvaluez' % i).val, getattr(p, 'vec%dvaluew' % i).val = num(v[2]), num(v[3])

def reset():
	S.clear()
	S.update(dict(t=0.0, flow=0.0, rot=0.0, rotV=0.0, twist=.15, hue=random.random(), colorMix=0.0, shockZ=-99.0, shockA=0.0,
		n1=6.0, n2=6.0, mixT=1.0, seqI=0, nextAt=0.0, beats=0, mirror=0.0, zoom=1.0, flash=0.0))

def morph(n):
	S['n1'] = S['n1'] if S['mixT'] < .5 else S['n2']
	S['n2'] = float(n); S['mixT'] = 0.0

def update(A, dt, now):
	if not S: reset()
	R = P('Reactivity'); on = 1 if A['on'] else 0; b = A['bands']; B = A['busy'] * on
	sp = P('Kspeed'); L = P('Klength')
	if A['kickHit']:                                    # kopák: rázová vlna vyletí ze dna tunelu ke kameře
		S['beats'] += 1
		S['shockZ'] = -L * .5; S['shockA'] = max(S['shockA'], (.25 + A['kickHit'] * .5) * R)
		S['flash'] = max(S['flash'], A['kickHit'] * .35 * R)
		if P('Lobes') == 0 and S['beats'] % 8 == 0:
			S['seqI'] = (S['seqI'] + 1) % len(SEQ); morph(SEQ[S['seqI']])
	if A['snareHit']:
		S['rotV'] += (1 if random.random() < .5 else -1) * A['snareHit'] * (.6 + B) * R
	tempo = A['tempo'] if (on and A['bpm']) else 1
	S['shockZ'] += dt * L * (.6 + tempo * .4)
	S['shockA'] *= math.exp(-dt * 1.2)
	S['flash'] *= math.exp(-dt * 8)
	S['rotV'] *= math.exp(-dt * 1.5)
	S['rot'] += dt * (.05 * sp + S['rotV'])
	S['t'] += dt * sp * (.15 + (A['energy'] * .4 + A['hatEnv'] * .6) * R * on)
	S['flow'] += dt * sp * (.02 + (.05 + B * .12) * tempo * on)
	tw = (P('Ktwist') * (.6 + (b['mid'] * .8 + A['centroid'] * .6) * R * on))
	S['twist'] += (tw - S['twist']) * (1 - math.exp(-dt * 1.5))
	S['hue'] += dt * (.02 + on * (.04 + A['centroid'] * .05) * R)
	S['colorMix'] += ((1 if P('Colour') else 0) - S['colorMix']) * (1 - math.exp(-dt * 2))
	lobes = int(P('Lobes'))
	if lobes == 0 and not on and now > S['nextAt']:
		S['seqI'] = (S['seqI'] + 1) % len(SEQ); morph(SEQ[S['seqI']]); S['nextAt'] = now + 7 / max(.3, sp)
	if lobes > 0 and S['n2'] != lobes: morph(lobes)
	S['mixT'] = min(1.0, S['mixT'] + dt * .5)
	m = S['mixT']; e = 4 * m ** 3 if m < .5 else 1 - (-2 * m + 2) ** 3 / 2
	lob = A['LOB'] if on else [.35 + .25 * math.sin(S['t'] * 2 + i) for i in range(12)]
	g = k('tube')
	setv(g, 0, (S['t'], S['twist'], L, .9 + b['sub'] * .15 * R * on))
	setv(g, 1, (S['n1'], S['n2'], e, P('Relief') * (.4 + b['low'] * .5 * R * on)))
	setv(g, 2, (S['shockZ'], S['shockA'], P('Ripple') * (.08 + (b['air'] * .1 + A['hatEnv'] * .08) * R * on), .9))
	setv(g, 3, (S['rot'], S['hue'], S['colorMix'], S['flow']))
	setv(g, 4, (P('Kbright') * (.8 + A['energy'] * .4 * on), S['flash'], 0, 0))
	setv(g, 5, tuple(lob[0:4])); setv(g, 6, tuple(lob[4:8])); setv(g, 7, tuple(lob[8:12]))
	rend = k('render')
	for name in ('mat',):
		setv(k(name), 0, (P('Ksize') * (1 + A['kickEnv'] * .4 * R * on), rend.width, rend.height, 3.0))
	# zrcadla: jedno se točí s energií hudby (roste do nekonečna, jako „audio reactive rotation“ z videa)
	S['mirror'] = (S['mirror'] + dt * (6 + (A['energy'] * 30 + B * 40) * R * on) * sp) % 360.0
	ang = [base + (S['mirror'] if i == 2 else S['mirror'] * .25 if i == 4 else 0) for i, base in enumerate(MIRRORS)]
	setv(k('mirrors'), 0, ang[0:4])
	setv(k('mirrors'), 1, (ang[4], P('Kaleido'), rend.width / max(1, rend.height), 0))
	S['zoom'] += ((1.0 + A['kickEnv'] * .02 * R * on) - S['zoom']) * (1 - math.exp(-dt * 6))
	fbx = k('fb_xf').par
	fbx.sx = fbx.sy = 1.0 + .012 * P('Feedback') * S['zoom']
	fbx.rotate = S['rotV'] * 2
	k('fb_lvl').par.opacity = min(.92, .82 * P('Feedback'))
