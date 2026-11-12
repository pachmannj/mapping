# DJ SHOW — hlavní smyčka (volá ji /project1/show/loop každý snímek)
# 1) analýza zvuku sdílená všemi scénami (pásma s automatickým ziskem, nástupy kopák/virbl/hihat, tempo, hustota)
# 2) režie: ruční / automatické střídání scén s prolínačkou
# 3) master: jas, odříznutí černé, maska plátna, záblesk, stroboskop, blackout, testovací obrazce
# 4) info a měřáky pro ovládací okno
import math, random, time, json, os
import numpy as np

SHOW = '/project1/show'
SCENES = ['krasohled', 'vortex', 'echoes', 'heat', 'membrane']
TESTS = {'off': 0, 'grid': 1, 'white': 2, 'frame': 3}

A = {}      # zvuk — čtou ho scény
D = {}      # režie a master

def O(name): return op(SHOW + '/' + name)
def P(name): return getattr(op(SHOW).par, name).eval()

def num(x):
	# TD 2025.33230 převádí subnormální čísla (např. doznívající záblesk 5e-324) na 1.8e308 → bílý obraz; NaN/inf taky pryč
	x = float(x)
	return 0.0 if x != x or abs(x) < 1e-12 or abs(x) > 1e12 else x

def setv(o, i, v):
	p = o.par
	getattr(p, 'vec%dvaluex' % i).val, getattr(p, 'vec%dvaluey' % i).val = num(v[0]), num(v[1])
	getattr(p, 'vec%dvaluez' % i).val, getattr(p, 'vec%dvaluew' % i).val = num(v[2]), num(v[3])

# ─────────────────────────── ZVUK ───────────────────────────
BANDS = dict(sub=(20, 60), kick=(60, 140), low=(140, 400), mid=(400, 2000), hmid=(2000, 6000), air=(6000, 14000))

def reset_audio():
	A.clear()
	A.update(dict(buf=np.zeros(2048, dtype=np.float32), on=False, level=0.0,
		bands={k: 0.0 for k in BANDS}, raw={k: 0.0 for k in BANDS}, mx={}, prev={}, armed={}, lastOn={},
		energy=0.0, centroid=.3, sustain=0.0, kickEnv=0.0, snareEnv=0.0, hatEnv=0.0,
		beats=0, snares=0, hats=0, kickHit=0.0, snareHit=0.0, bpm=0.0, tempo=1.0, ioi=[], lastKick=0.0, hits=[], busy=0.0,
		LOB=np.full(12, .35), linked=False, silentFor=99.0,
		vx=dict(sub=0., kick=0., snare=0., vocal=0., hihat=0., cymbal=0.), vxs={}, vxp={}))

def onset(name, v, now, dt, gap, thr):
	slow = A['prev'].get(name, v); d = v - slow
	A['prev'][name] = slow + (v - slow) * (1 - math.exp(-dt * 4))
	if d < thr * .4: A['armed'][name] = True
	if A['armed'].get(name, True) and d > thr and now - A['lastOn'].get(name, 0) > gap:
		A['armed'][name] = False; A['lastOn'][name] = now
		return min(1.0, .35 + d * 2.2)
	return 0.0

def read_input():
	src = O('a_in')
	try:
		arr = src.numpyArray()
	except Exception:
		return None, 44100
	if arr is None or arr.size == 0: return None, 44100
	x = arr.mean(axis=0) if arr.ndim > 1 else arr
	return x.astype(np.float32) * P('Gain'), src.rate

def analyse(now, dt):
	A['kickEnv'] *= math.exp(-dt * 3.5); A['snareEnv'] *= math.exp(-dt * 5); A['hatEnv'] *= math.exp(-dt * 8)
	A['kickHit'] = 0.0; A['snareHit'] = 0.0
	x, sr = read_input()
	peak = float(np.abs(x).max()) if x is not None and len(x) else 0.0
	A['level'] += (min(1.0, peak) - A['level']) * .3
	if peak < 1e-3:                                   # ticho / odpojený kabel → scény přejdou do klidového režimu
		A['silentFor'] += dt
		if A['silentFor'] > .5: A['on'] = False
		for k in A['bands']: A['bands'][k] *= .94
		for k in A['vx']: A['vx'][k] *= .9
		A['energy'] *= .94; A['busy'] *= .97
		return
	A['silentFor'] = 0.0; A['on'] = True
	buf = np.concatenate([A['buf'], x])[-2048:]; A['buf'] = buf
	spec = np.clip(np.abs(np.fft.rfft(buf * np.hanning(len(buf)))) / 64.0, 0, 1)
	nb = len(spec)
	def binr(lo, hi):
		a = max(1, int(lo / (sr / 2) * nb)); b = max(a + 1, int(hi / (sr / 2) * nb)); return a, min(b, nb)
	for k, (lo, hi) in BANDS.items():
		a, b = binr(lo, hi); v = float(spec[a:b].mean())
		A['mx'][k] = max(v, A['mx'].get(k, .2) * .9985, .02)
		nv = min(1.0, v / A['mx'][k]); A['raw'][k] = nv
		A['bands'][k] += (nv - A['bands'][k]) * (1 - math.exp(-dt * 7))
	tot = float(spec[1:].sum())
	A['centroid'] += ((float((spec[1:] * np.arange(1, nb)).sum()) / tot / nb * 4 if tot else 0) - A['centroid']) * .08
	rms = float(np.sqrt(np.mean(x * x))); A['mx']['rms'] = max(rms, A['mx'].get('rms', .1) * .999, .01)
	A['energy'] += (rms / A['mx']['rms'] - A['energy']) * .2
	R = A['raw']
	k = onset('kick', R['kick'] * .7 + R['sub'] * .3, now, dt, .18, .16)
	if k:
		A['kickEnv'] = max(A['kickEnv'], k); A['kickHit'] = k; A['hits'].append(now)
		if not A['linked']: A['beats'] += 1
		gapk = now - A['lastKick']; A['lastKick'] = now
		if .25 < gapk < 1.5:
			A['ioi'].append(gapk); A['ioi'] = A['ioi'][-10:]
		if len(A['ioi']) > 3 and not A['linked']:
			m = sorted(A['ioi'])[len(A['ioi']) // 2]; A['bpm'] = 60 / m
			A['tempo'] = max(.45, min(2.4, (A['bpm'] / 110) ** 1.4))
	sn = onset('snare', R['mid'] * .75 + R['hmid'] * .25, now, dt, .23, .22)
	if sn: A['snareEnv'] = max(A['snareEnv'], sn); A['snareHit'] = sn; A['snares'] += 1; A['hits'].append(now)
	ht = onset('hat', R['air'], now, dt, .08, .14)
	if ht: A['hatEnv'] = max(A['hatEnv'], ht); A['hats'] += 1; A['hits'].append(now)
	b = A['bands']
	flux = abs(b['mid'] - A['prev'].get('midS', b['mid'])); A['prev']['midS'] = b['mid']
	A['sustain'] += ((1 if b['mid'] > .55 and flux < .02 else 0) - A['sustain']) * .02
	raw = np.zeros(12)                               # 12 logaritmických pásem 50 Hz – 9 kHz (laloky Krasohledu)
	for i in range(12):
		lo = 50 * 180 ** (i / 12); hi = 50 * 180 ** ((i + 1) / 12); a, bb = binr(lo, hi)
		raw[i] = float(spec[a:bb].mean()) * (1 + i * .12)
	A['mx']['lob'] = max(float(raw.max()), A['mx'].get('lob', .2) * .997, .02)
	v = np.minimum(1, raw / A['mx']['lob'])
	rate = np.where(v > A['LOB'], 9.0, 2.5)
	A['LOB'] += (v - A['LOB']) * (1 - np.exp(-dt * rate))
	act = sum(min(1, max(0, (b[kk] - .3) / .4)) for kk in b) / 6
	A['hits'] = [h for h in A['hits'] if now - h < 2]
	busyT = min(1, act * .55 + min(1, len(A['hits']) / 2 / 7) * .3 + A['energy'] * .25)
	A['busy'] += (busyT - A['busy']) * (1 - math.exp(-dt * (1.6 if busyT > A['busy'] else .6)))
	# pásma ve stylu webového Vortexu (bajtové spektrum 0–1): stlačený rozsah, ať nástupy nejsou přestřelené
	vx = A['vx']
	for name, key in (('sub', 'sub'), ('kick', 'kick'), ('snare', 'low'), ('vocal', 'mid'), ('hihat', 'hmid'), ('cymbal', 'air')):
		vx[name] = .6 * b[key] ** 1.5

def link_sync():
	L = O('link')
	if not L: return False
	L.par.enable = bool(P('Link'))
	if not P('Link'): return False
	try:
		if L['numpeers'] is None or L['numpeers'].eval() < 1: return False
		bpm = float(L['tempo'].eval()); beat = int(L['beat'].eval())
	except Exception:
		return False
	A['bpm'] = bpm; A['tempo'] = max(.45, min(2.4, (bpm / 110) ** 1.4))
	if beat != A.get('linkBeat'):
		A['linkBeat'] = beat; A['beats'] += 1
	return True

# ─────────────────────────── REŽIE ───────────────────────────
def scene_list():
	s = [n for n in str(P('Autoscenes')).replace(',', ' ').split() if n in SCENES]
	return s or SCENES

def direct(now, dt):
	if 'cur' not in D:
		D.update(dict(cur=SCENES[0], prev=SCENES[0], x=1.0, b0=0, t0=now, flash=0.0, bo=0.0, lastBeat=0))
	sel = P('Scene')
	if sel == 'auto':
		lst = scene_list()
		target = D['cur'] if D['cur'] in lst else lst[0]
		bars = max(1, int(P('Autobars')))
		byBeat = A['on'] and A['beats'] - D['b0'] >= bars * 4
		byTime = now - D['t0'] > max(10.0, P('Autotime')) and (not A['on'] or A['beats'] - D['b0'] < 2)
		if byBeat or byTime:
			target = lst[(lst.index(target) + 1) % len(lst)] if target in lst else lst[0]
	else:
		target = sel
	if target != D['cur']:
		D['prev'] = D['cur'] if D['x'] >= .5 else D['prev']
		D['cur'] = target; D['x'] = 0.0; D['b0'] = A['beats']; D['t0'] = now
	D['x'] = min(1.0, D['x'] + dt / max(.05, P('Fade')))
	e = D['x'] * D['x'] * (3 - 2 * D['x'])
	O('selA').par.index = SCENES.index(D['prev'] if D['x'] < 1 else D['cur'])
	O('selB').par.index = SCENES.index(D['cur'])
	O('xfade').par.cross = e

def active_scenes():
	return {D['cur']} | ({D['prev']} if D['x'] < 1 else set())

# ─────────────────────────── MASTER ───────────────────────────
def master(dt):
	if A['kickHit'] and P('Strobe'): D['flash'] = max(D['flash'], .85)
	D['flash'] *= math.exp(-dt * 9)
	bo = 1.0 if P('Blackout') else 0.0
	D['bo'] += (bo - D['bo']) * (1 - math.exp(-dt * 14))
	tp = TESTS.get(P('Testpattern'), 0)
	setv(O('master'), 0, (P('Master'), P('Blackcrush'), D['flash'], D['bo']))
	setv(O('master'), 1, (P('Maskl'), P('Maskr'), P('Maskt'), P('Maskb')))
	setv(O('master'), 2, (P('Feather'), tp if tp < 3 else 0, 0, absTime.seconds))
	setv(O('outfix'), 0, (tp, absTime.seconds, 0, 0))

def flash():
	if D: D['flash'] = 1.0

# ─────────────────────────── UI ───────────────────────────
def ui(now, dt):
	b = A['bands']
	setv(O('ui_meters'), 0, (b['sub'], b['kick'], b['low'], b['mid']))
	setv(O('ui_meters'), 1, (b['hmid'], b['air'], A['kickEnv'], A['snareEnv']))
	setv(O('ui_meters'), 2, (A['hatEnv'], A['energy'], A['busy'], 1 if A['on'] else 0))
	D['fps'] = D.get('fps', 60) * .95 + (1 / max(dt, 1e-3)) * .05
	if now - D.get('infoT', 0) < .25: return
	D['infoT'] = now
	src = 'SOUBOR: ' + os.path.basename(str(O('a_file').par.file.eval())) if P('Source') == 'file' else 'LIVE: ' + str(O('a_live').par.device.eval())
	lines = [
		'SCÉNA  %s%s%s' % (D['cur'].upper(), '  ← %s' % D['prev'] if D['x'] < 1 else '', '  (auto)' if P('Scene') == 'auto' else ''),
		'ZVUK   %s   %s' % ('SIGNÁL OK' if A['on'] else '!! TICHO / ŽÁDNÝ SIGNÁL', src[:60]),
		'TEMPO  %s%s   úroveň %.2f' % ('%d bpm' % round(A['bpm']) if A['bpm'] else '— bpm', '  · LINK' if A['linked'] else '', A['level']),
		'VÝSTUP %s   %d fps   %dx%d   %s' % ('PROJEKTOR ZAP' if O('projector').isOpen else 'projektor vyp', round(D['fps']),
		         O('final').width, O('final').height, ('TEST: ' + P('Testpattern')) if P('Testpattern') != 'off' else ''),
		('!! BLACKOUT   ' if P('Blackout') else '') + ('STROBO   ' if P('Strobe') else ''),
		'1–5 scéna  0 auto  B blackout  F záblesk  S strobo  T test  N skladba  O projektor',
	]
	O('info').text = '\n'.join(lines)

# ─────────────────────────── HLÍDÁNÍ ZAŘÍZENÍ ───────────────────────────
# Zvukový vstup a kamera se po zapnutí / změně zařízení občas neinicializují → vypnout a o 2 snímky později zapnout.
# Když živý vstup 5 s nedává žádný signál (vytažená zvukovka, změna zařízení v systému), zkusí se znovu otevřít.
# Odposlech demo hudby: když se nepřipojí, zkusí to znovu (a z „default“ přejde na první skutečné zařízení).
def reinit(name, want):
	o = O(name)
	o.par.active = False
	for pn in ('refresh', 'refreshdevices'):                  # znovu načíst seznam zařízení (např. nově připojená zvukovka)
		p = getattr(o.par, pn, None)
		if p is not None and p.isPulse: p.pulse()
	D['re_' + name] = (2, want)

def devices(now):
	live = P('Source') == 'live'
	key = (live, P('Inputdevice'))
	if key != D.get('akey'):
		D['akey'] = key; reinit('a_live', live); D['aT'] = now
	elif live and A['silentFor'] > 5 and now - D.get('aT', 0) > 5:
		D['aT'] = now; reinit('a_live', True)
		debug('živý vstup bez signálu → znovu otevírám', P('Inputdevice'))
	cam = bool(P('Camera') or P('Previz'))
	key = (cam, P('Cameradevice'))
	if key != D.get('ckey'):
		D['ckey'] = key; reinit('cam_in', cam)
	mon = bool(P('Source') == 'file' and P('Monitor'))
	key = (mon, P('Outputdevice'))
	if key != D.get('okey'):
		D['okey'] = key; D['oT'] = now; D['ofb'] = False
		O('a_out').par.device = P('Outputdevice'); reinit('a_out', mon)
	elif mon and now - D.get('oT', 0) > 5 and O('a_out').warnings():
		D['oT'] = now; o = O('a_out')
		if P('Outputdevice') == 'default' and not D['ofb']:    # „default“ se nepřipojil → první skutečné zařízení
			names = [n for n, l in zip(o.par.device.menuNames, o.par.device.menuLabels) if n != 'default' and 'Teams' not in l]
			if names: o.par.device = names[0]; D['ofb'] = True
		reinit('a_out', True)
		debug('odposlech se nepřipojil → znovu otevírám', o.par.device.eval())
	for name in ('a_live', 'cam_in', 'a_out'):
		r = D.get('re_' + name)
		if r:
			n, want = r
			if n <= 0: O(name).par.active = want; D['re_' + name] = None
			else: D['re_' + name] = (n - 1, want)

# ─────────────────────────── HLAVNÍ KROK ───────────────────────────
def step():
	if not A: reset_audio()
	now = time.time(); dt = min(.05, now - D.get('last', now - 1 / 60)); D['last'] = now
	A['linked'] = link_sync()
	devices(now)
	analyse(now, dt)
	direct(now, dt)
	for name in active_scenes():
		try:
			O('sc_' + name).module.update(A, dt, now)
		except Exception as e:
			if now - D.get('errT', 0) > 2:
				D['errT'] = now; debug('scéna %s: %s' % (name, e))
	master(dt)
	ui(now, dt)

# ─────────────────────────── MAPOVÁNÍ: ULOŽIT / NAČÍST ───────────────────────────
MAPPARS = ['Pintl', 'Pintr', 'Pinbl', 'Pinbr', 'Maskl', 'Maskr', 'Maskt', 'Maskb', 'Feather', 'Fliph', 'Flipv', 'Blackcrush', 'Master',
           'Prevtl', 'Prevtr', 'Prevbl', 'Prevbr']

def map_file():
	f = str(P('Mapfile')).strip()
	return f if f else project.folder + '/mapping.json'

def save_mapping():
	S = op(SHOW); data = {}
	for n in MAPPARS:
		g = getattr(S.parGroup, n, None)
		data[n] = [p.eval() for p in g] if g is not None and len(g) > 1 else getattr(S.par, n).eval()
	with open(map_file(), 'w', encoding='utf-8') as f: json.dump(data, f, indent=1)
	print('mapování uloženo:', map_file())

def load_mapping():
	S = op(SHOW)
	try:
		data = json.load(open(map_file(), encoding='utf-8'))
	except Exception as e:
		print('mapování nenalezeno:', map_file(), e); return
	for n, v in data.items():
		if isinstance(v, list):
			for p, x in zip(getattr(S.parGroup, n), v): p.val = x
		elif hasattr(S.par, n):
			getattr(S.par, n).val = v
	print('mapování načteno:', map_file())

def reset_mapping():
	S = op(SHOW)
	for n, v in (('Pintl', (0, 1)), ('Pintr', (1, 1)), ('Pinbl', (0, 0)), ('Pinbr', (1, 0)),
	             ('Prevtl', (.3, .75)), ('Prevtr', (.7, .75)), ('Prevbl', (.3, .3)), ('Prevbr', (.7, .3))):
		for p, x in zip(getattr(S.parGroup, n), v): p.val = x
	for n in ('Maskl', 'Maskr', 'Maskt', 'Maskb'): getattr(S.par, n).val = 0
	S.par.Feather = .02

# ─────────────────────────── VÝSTUP NA PROJEKTOR ───────────────────────────
def open_output():
	w = O('projector')
	mons = list(monitors)
	idx = int(P('Outmonitor'))
	if idx < 0 or idx >= len(mons): idx = len(mons) - 1      # výchozí: poslední připojený monitor = projektor
	m = mons[idx]
	w.par.justifyoffsetto = 'specifydisplay'
	w.par.display = idx
	w.par.size = 'fill'
	w.par.winopen.pulse()
	print('projektor: monitor %d %dx%d%s' % (idx, m.width, m.height, ' (POZOR: jen hlavní displej)' if len(mons) < 2 else ''))

def close_output():
	O('projector').par.winclose.pulse()
