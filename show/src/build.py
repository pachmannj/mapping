# DJ SHOW — sestaví celou show v TouchDesigneru do /project1/show.
# Spuštění: Textport (Option+T) →  exec(open(project.folder + '/src/build.py').read())
# Je idempotentní: starou /project1/show smaže a postaví znovu, hodnoty ovládacích parametrů (i mapování) zachová.
import os

SRC = 'src'                     # relativní cesty vůči složce projektu → složku show jde přesunout / zkopírovat
GL = SRC + '/glsl'
SCENES = ['krasohled', 'vortex', 'echoes', 'heat', 'bird', 'flower']
RES = "op('/project1/show').par.Resw", "op('/project1/show').par.Resh"
LOG = []

def setp(o, name, val):
	p = getattr(o.par, name, None)
	if p is None:
		LOG.append('chybí parametr %s.%s' % (o.path, name)); return False
	try:
		p.val = val; return True
	except Exception as e:
		LOG.append('nelze nastavit %s.%s = %r (%s)' % (o.path, name, val, e)); return False

def expr(o, name, e):
	p = getattr(o.par, name, None)
	if p is None: LOG.append('chybí parametr %s.%s' % (o.path, name)); return
	p.expr = e

def mk(parent, typ, name, x, y, inputs=()):
	o = parent.create(typ, name); o.nodeX, o.nodeY = x, y
	for i, src in enumerate(inputs):
		if src is not None: o.inputConnectors[i].connect(src)
	return o

def textfile(parent, name, path, x, y):
	d = mk(parent, textDAT, name, x, y); d.par.file = path; setp(d, 'syncfile', True)
	try: d.par.loadonstartpulse.pulse()
	except Exception: pass
	return d

def res(o, fmt=None):
	setp(o, 'outputresolution', 'custom'); expr(o, 'resolutionw', RES[0]); expr(o, 'resolutionh', RES[1])
	if fmt: setp(o, 'format', fmt)

def uniforms(o, names):
	o.seq.vec.numBlocks = len(names)
	for i, u in enumerate(names): setp(o, 'vec%dname' % i, u)

def glsl(parent, name, file, x, y, names, inputs=(), fmt='rgba16float', custom_res=False):
	d = textfile(parent, name + '_dat', GL + '/' + file, x, y - 130)
	g = mk(parent, glslmultiTOP if len(inputs) > 3 else glslTOP, name, x, y, inputs)   # GLSL TOP má jen 3 vstupy
	g.par.pixeldat = d
	setp(g, 'format', fmt)
	if custom_res or not inputs: res(g)
	if names: uniforms(g, names)
	return g

# ─────────────── zachovat hodnoty parametrů z předchozí verze ───────────────
R = op('/project1')
saved = {}
old = R.op('show')
if old:
	for p in old.customPars:                 # přenáší se jen nastavení show, ne scén (ty mají vlastní výchozí hodnoty)
		if p.mode == ParMode.CONSTANT and not p.isPulse and p.page.name in ('Show', 'Audio', 'Mapping', 'Output', 'Camera'): saved[p.name] = p.val
	try: old.op('projector').par.winclose.pulse()
	except Exception: pass
	old.destroy()
SH = R.create(baseCOMP, 'show'); SH.nodeX, SH.nodeY = 0, 0
SH.color = (.15, .45, .7)

# ─────────────── ovládací parametry ───────────────
def page(n): return SH.appendCustomPage(n)
def F(pg, name, label, d, lo, hi, clamp=True):
	p = pg.appendFloat(name, label=label)[0]; p.default = d; p.val = d; p.normMin, p.normMax = lo, hi
	if clamp: p.clampMin = True; p.min = lo
	return p
def I(pg, name, label, d, lo, hi):
	p = pg.appendInt(name, label=label)[0]; p.default = d; p.val = d; p.normMin, p.normMax = lo, hi; return p
def T(pg, name, label, d=False):
	p = pg.appendToggle(name, label=label)[0]; p.default = d; p.val = d; return p
def M(pg, name, label, names, labels, d=None):
	p = pg.appendMenu(name, label=label)[0]; p.menuNames = names; p.menuLabels = labels; p.default = d or names[0]; p.val = d or names[0]; return p
def PU(pg, name, label): return pg.appendPulse(name, label=label)[0]
def XY(pg, name, label, d):
	ps = pg.appendXY(name, label=label)
	for p, v in zip(ps, d): p.default = v; p.val = v; p.normMin, p.normMax = -.25, 1.25
	return ps

pg = page('Show')
M(pg, 'Scene', 'Scéna', ['auto'] + SCENES, ['AUTO (střídá se)', 'Krasohled', 'Vortex', 'Echoes', 'Heat', 'Pták', 'Květ'], 'auto')
p = pg.appendStr('Autoscenes', label='Auto: pořadí scén')[0]; p.default = p.val = ' '.join(SCENES)
I(pg, 'Autobars', 'Auto: změna po taktech', 16, 4, 64)
F(pg, 'Autotime', 'Auto: změna bez beatu (s)', 45, 10, 180)
F(pg, 'Fade', 'Prolínačka (s)', 3, 0, 10)
F(pg, 'Master', 'Master jas', 1, 0, 1.5)
F(pg, 'Reactivity', 'Reaktivita na hudbu', 1, 0, 1.5)
T(pg, 'Colour', 'Barva (jinak bílá/modrá)', False)
T(pg, 'Blackout', 'BLACKOUT  [B]', False)
T(pg, 'Strobe', 'Stroboskop na kopák  [S]', False)
PU(pg, 'Flash', 'Záblesk  [F]')

pg = page('Audio')
M(pg, 'Source', 'Zdroj zvuku', ['file', 'live'], ['Demo soubory (složka music)', 'Živý vstup (linka z mixu)'], 'file')
p = pg.appendStrMenu('Inputdevice', label='Vstupní zařízení')[0]; p.menuSource = "op('./a_live').par.device"; p.default = p.val = 'default'
F(pg, 'Gain', 'Zesílení vstupu', 1, 0, 8)
p = pg.appendFolder('Musicfolder', label='Složka s hudbou (prázdné = ../music)')[0]; p.default = p.val = ''
I(pg, 'Track', 'Skladba č.', 0, 0, 20)
PU(pg, 'Next', 'Další skladba  [N]')
F(pg, 'Volume', 'Hlasitost odposlechu', .8, 0, 1)
p = pg.appendStrMenu('Outputdevice', label='Výstup odposlechu')[0]; p.menuSource = "op('./a_out').par.device"; p.default = p.val = 'default'
T(pg, 'Monitor', 'Přehrávat demo do repráků', True)
T(pg, 'Link', 'Ableton Link (tempo z DJ softwaru)', False)

pg = page('Mapping')
M(pg, 'Testpattern', 'Testovací obrazec  [T]', ['off', 'grid', 'white', 'frame'],
  ['Vypnuto', 'Mřížka plátna (barevné rohy)', 'Celá bílá (ostření/jas)', 'Rámeček projektoru'], 'off')
T(pg, 'Fliph', 'Zrcadlit vodorovně (zadní projekce)', False)
T(pg, 'Flipv', 'Zrcadlit svisle (projektor vzhůru nohama)', False)
XY(pg, 'Pintl', 'Roh vlevo nahoře', (0, 1)); XY(pg, 'Pintr', 'Roh vpravo nahoře', (1, 1))
XY(pg, 'Pinbl', 'Roh vlevo dole', (0, 0)); XY(pg, 'Pinbr', 'Roh vpravo dole', (1, 0))
for n, l in (('Maskl', 'Maska vlevo'), ('Maskr', 'Maska vpravo'), ('Maskt', 'Maska nahoře'), ('Maskb', 'Maska dole')): F(pg, n, l, 0, 0, .5)
F(pg, 'Feather', 'Měkkost okraje masky', .02, 0, .2)
F(pg, 'Blackcrush', 'Odříznutí černé (čisté plátno)', .03, 0, .2)
p = pg.appendFile('Mapfile', label='Soubor mapování')[0]; p.default = p.val = ''
PU(pg, 'Savemap', 'Uložit mapování'); PU(pg, 'Loadmap', 'Načíst mapování'); PU(pg, 'Resetmap', 'Reset mapování')

pg = page('Output')
I(pg, 'Outmonitor', 'Monitor projektoru (-1 = poslední)', -1, -1, 4)
PU(pg, 'Openoutput', 'Otevřít výstup na projektor  [O]'); PU(pg, 'Closeoutput', 'Zavřít výstup na projektor')
T(pg, 'Autooutput', 'Po spuštění otevřít výstup (je-li projektor)', True)
I(pg, 'Resw', 'Rozlišení – šířka', 1280, 320, 1280); I(pg, 'Resh', 'Rozlišení – výška', 720, 180, 1280)
PU(pg, 'Opencontrol', 'Otevřít ovládací okno')

pg = page('Camera')
T(pg, 'Camera', 'Kamera zapnutá (iPhone / webkamera)', False)
p = pg.appendStrMenu('Cameradevice', label='Kamera')[0]; p.menuSource = "op('./cam_in').par.device"
T(pg, 'Previz', 'Previz: promítnout obraz do záběru kamery', False)
p = pg.appendFile('Previzimage', label='Previz: fotka místa (místo živé kamery)')[0]; p.default = p.val = ''
XY(pg, 'Prevtl', 'Previz roh vlevo nahoře', (.3, .75)); XY(pg, 'Prevtr', 'Previz roh vpravo nahoře', (.7, .75))
XY(pg, 'Prevbl', 'Previz roh vlevo dole', (.3, .3)); XY(pg, 'Prevbr', 'Previz roh vpravo dole', (.7, .3))
F(pg, 'Prevdim', 'Previz: ztmavení pozadí', .6, 0, 1)

pg = page('Krasohled')
p = I(pg, 'Lobes', 'Laloky (0 = auto)', 0, 0, 12); p.clampMin = p.clampMax = True; p.min, p.max = 0, 12
F(pg, 'Relief', 'Hloubka laloků', .5, 0, 1.5); F(pg, 'Ktwist', 'Zkroucení tunelu', .15, 0, 1)
F(pg, 'Ripple', 'Šum', 1, 0, 3); F(pg, 'Klength', 'Délka tunelu', 8, 2, 20); F(pg, 'Kspeed', 'Rychlost', 1, 0, 3)
p = I(pg, 'Kaleido', 'Zrcadla (0–5)', 3, 0, 5); p.clampMin = p.clampMax = True; p.min, p.max = 0, 5
F(pg, 'Feedback', 'Stopy', 1, 0, 1.1); F(pg, 'Bloom', 'Záře', 1, 0, 2); F(pg, 'Ksize', 'Velikost bodů (px)', 2, .5, 6); F(pg, 'Kbright', 'Jas', 1, 0, 3)

pg = page('Vortex')
I(pg, 'Vcount', 'Max. částic', 600000, 20000, 600000); F(pg, 'Vbirth', 'Rychlost zrodu', .57, 0, 3)
F(pg, 'Vbright', 'Jas', 3.324, 0, 5); F(pg, 'Vsize', 'Velikost částic', 1.476, .5, 8); F(pg, 'Vtrails', 'Stopy', .624, 0, 1.1)
F(pg, 'Vturb', 'Turbulence', 2.446, 0, 3); F(pg, 'Vzoom', 'Vzdálenost kamery', .4, .4, 2)

pg = page('Echoes')
F(pg, 'Epixel', 'Pixelace (základ)', .15, 0, .15); F(pg, 'Edisp', 'Posunutí (displace)', .0076, 0, .5)
F(pg, 'Etrails', 'Ozvěny (stopy)', 0, 0, .97); F(pg, 'Ebright', 'Jas', 1.984, 0, 3)
F(pg, 'Epixmusic', 'Pixelace podle hudby', 2, 0, 2)

pg = page('Pták')
M(pg, 'Blook', 'Look', ['auto', 'real', 'chrono', 'slit', 'ink', 'kaleido'], ['AUTO (režisér podle hudby)', 'Reál (fotka)', 'Chronofoto (kopie v čase)', 'Slit-scan (čas po pixelech)', 'Inkoust / kouř', 'Kaleidoskop'], 'auto')
F(pg, 'Babstract', 'Abstrakce', .6, 0, 1)
F(pg, 'Bflap', 'Síla máchnutí', 1, 0, 2); F(pg, 'Bdissolve', 'Rozpad na částice', 1, 0, 2); F(pg, 'Btrails', 'Stopy', .8, 0, 1.1)
F(pg, 'Bspeed', 'Rychlost videa', 1, 0, 3); F(pg, 'Bsize', 'Velikost částic (px)', 1.6, .5, 5); F(pg, 'Bbright', 'Jas', 1.2, 0, 3)

pg = page('Květ')
p = I(pg, 'Fpetals', 'Počet lístků', 89, 21, 600); p.clampMin = p.clampMax = True; p.min, p.max = 40, 600
F(pg, 'Fbloom', 'Rozkvět', 1, 0, 1.5); F(pg, 'Fsize', 'Velikost', .95, .3, 2); F(pg, 'Fcup', 'Prohnutí lístků', 1, 0, 2)
F(pg, 'Fspin', 'Otáčení', 1, 0, 3); F(pg, 'Fbright', 'Jas', 1.2, 0, 4)

pg = page('Heat')
F(pg, 'Hlife', 'Životnost bodů (s)', 1, 1, 25); F(pg, 'Hflow', 'Proudění', .701, 0, 3); F(pg, 'Hrise', 'Stoupání tepla', 0, 0, 3)
F(pg, 'Hrows', 'Řad cihel', 100, 10, 100); F(pg, 'Hsize', 'Velikost bodů (px)', 2.384, .5, 6); F(pg, 'Hbright', 'Jas', 2.634, 0, 4)

for n, v in saved.items():
	if hasattr(SH.par, n):
		try: getattr(SH.par, n).val = v
		except Exception: pass

SH.par.Autoscenes = ' '.join([n for n in SH.par.Autoscenes.eval().split() if n in SCENES] + [n for n in SCENES if n not in SH.par.Autoscenes.eval().split()])   # pořadí auto režimu = jen existující scény

# ─────────────── zvuk ───────────────
pl = mk(SH, folderDAT, 'playlist', -1400, 600)
expr(pl, 'rootfolder', "parent().par.Musicfolder or tdu.expandPath(project.folder + '/../music')")
setp(pl, 'allextensions', False); setp(pl, 'audioextensions', True)
af = mk(SH, audiofileinCHOP, 'a_file', -1400, 450)
expr(af, 'file', "op('playlist')[int(parent().par.Track) % max(1, op('playlist').numRows - 1) + 1, 'path'] if op('playlist').numRows > 1 else ''")
setp(af, 'playmode', 'sequential'); setp(af, 'repeat', 'on'); setp(af, 'play', True)
expr(af, 'play', "parent().par.Source == 'file'")
al = mk(SH, audiodeviceinCHOP, 'a_live', -1400, 300)
setp(al, 'active', False); expr(al, 'device', "parent().par.Inputdevice")      # zapíná engine.devices()
setp(al, 'format', 'stereo'); setp(al, 'ratemode', 'auto')
sw = mk(SH, switchCHOP, 'a_src', -1200, 380, (af, al)); expr(sw, 'index', "1 if parent().par.Source == 'live' else 0")
ain = mk(SH, nullCHOP, 'a_in', -1000, 380, (sw,))
mon = mk(SH, mathCHOP, 'a_mon', -1200, 520, (af,)); expr(mon, 'gain', "parent().par.Volume")
aout = mk(SH, audiodeviceoutCHOP, 'a_out', -1000, 520, (mon,)); setp(aout, 'active', False)          # zapíná engine.devices()
lk = mk(SH, abletonlinkCHOP, 'link', -1400, 150)
for n in ('tempo', 'beat'): setp(lk, n, True)
setp(lk, 'enable', False)

# ─────────────── engine a moduly scén ───────────────
textfile(SH, 'engine', SRC + '/engine.py', -800, 600)
for i, n in enumerate(SCENES): textfile(SH, 'sc_' + n, SRC + '/sc_%s.py' % n, -800 + i * 150, 450)
info = mk(SH, textDAT, 'info', -200, 600)
lp = mk(SH, executeDAT, 'loop', -650, 600)
lp.text = "def onFrameStart(frame):\n\top('engine').module.step()\n\treturn\n"
setp(lp, 'framestart', True); setp(lp, 'active', True)
st = mk(SH, executeDAT, 'startup', -500, 600)
st.text = '''import os
def onStart():
	E = op('engine').module
	if os.path.exists(E.map_file()): E.load_mapping()
	if parent().par.Autooutput and len(monitors) > 1: run("op('%s').module.open_output()" % op('engine').path, delayFrames=30)
	run("op('%s').par.winopen.pulse()" % op('control').path, delayFrames=10)
	return
'''
setp(st, 'start', True)
ctl = mk(SH, parameterexecuteDAT, 'controls', -350, 600)
setp(ctl, 'op', SH.path); setp(ctl, 'pars', '*'); setp(ctl, 'onpulse', True); setp(ctl, 'valuechange', False)
ctl.text = '''def onPulse(par):
	S = par.owner; E = op('engine').module; n = par.name
	if n == 'Next': S.par.Track = int(S.par.Track) + 1
	elif n == 'Flash': E.flash()
	elif n == 'Openoutput': E.open_output()
	elif n == 'Closeoutput': E.close_output()
	elif n == 'Savemap': E.save_mapping()
	elif n == 'Loadmap': E.load_mapping()
	elif n == 'Resetmap': E.reset_mapping()
	elif n == 'Opencontrol': op('control').par.winopen.pulse()
	return
'''
kb = mk(SH, keyboardinDAT, 'keys', -200, 450)
kcb = mk(SH, textDAT, 'keys_cb', -200, 330)
kcb.text = '''# klávesové zkratky (fungují, když je aktivní okno TouchDesigneru nebo ovládací okno)
TESTS = ['off', 'grid', 'white', 'frame']
def onKey(dat, keyInfo):
	f = keyInfo._asdict() if hasattr(keyInfo, '_asdict') else {}
	if not f.get('state', getattr(keyInfo, 'state', True)): return
	if f.get('ctrl') or f.get('alt') or f.get('cmd'): return
	c = str(f.get('character', getattr(keyInfo, 'character', '')) or '').lower()
	S = parent(); E = op('engine').module
	scenes = ['auto', 'krasohled', 'vortex', 'echoes', 'heat', 'bird', 'flower']
	if c in '0123456' and c: S.par.Scene = scenes[int(c)]
	elif c == 'b': S.par.Blackout = not S.par.Blackout
	elif c == 's': S.par.Strobe = not S.par.Strobe
	elif c == 'f': E.flash()
	elif c == 'n': S.par.Track = int(S.par.Track) + 1
	elif c == 't': S.par.Testpattern = TESTS[(TESTS.index(S.par.Testpattern.eval()) + 1) % len(TESTS)]
	elif c == 'o': E.open_output()
	return
'''
setp(kb, 'callbacks', kcb.path)

# ─────────────── kamera (iPhone přes Continuity Camera / webkamera) ───────────────
cam = mk(SH, videodeviceinTOP, 'cam_in', -1400, -1100)
setp(cam, 'active', False)                                                    # zapíná engine.devices()
expr(cam, 'device', "parent().par.Cameradevice")

# ─────────────── scény (src/build_scenes.py) ───────────────
exec(open(SRC + '/build_scenes.py', encoding='utf-8').read())
SKIP = globals().get('SKIP_SCENES', ())                         # ladění: scény, které se mají vynechat
for nm, fn in (('krasohled', build_krasohled), ('vortex', build_vortex), ('echoes', build_echoes), ('heat', build_heat), ('bird', build_bird), ('flower', build_flower)):
	if nm in SKIP:
		X = mk(SH, baseCOMP, nm, -1100, 0); mk(X, constantTOP, 'out1', 0, 0)
	else: fn(SH)

# ─────────────── mix scén, master, mapování ───────────────
outs = []
for i, n in enumerate(SCENES):                       # sítě scén jsou o úroveň níž → do mixu přes Select TOP
	o = mk(SH, selectTOP, 'in_' + n, -900, 0 - i * 150); o.par.top = SH.op(n + '/out1'); outs.append(o)
sels = []
for i, n in enumerate(('selA', 'selB')):
	s = mk(SH, switchTOP, n, -800, -100 - i * 200)
	for j, o in enumerate(outs): s.inputConnectors[j].connect(o)
	sels.append(s)
xf = mk(SH, crossTOP, 'xfade', -600, -200, sels)
ms = glsl(SH, 'master', 'master.glsl', -400, -200, ['uM0', 'uM1', 'uM2'], (xf,), 'rgba8fixed')
fl = mk(SH, flipTOP, 'flip', -200, -200, (ms,)); expr(fl, 'flipx', "parent().par.Fliph"); expr(fl, 'flipy', "parent().par.Flipv")
pin = mk(SH, cornerpinTOP, 'pin', 0, -200, (fl,))
for corner, par in (('topleft', 'Pintl'), ('topright', 'Pintr'), ('botleft', 'Pinbl'), ('botright', 'Pinbr')):
	setp(pin, 'pin%sunit' % corner, 'fraction')
	expr(pin, 'pin%sx' % corner, "parent().par.%sx" % par); expr(pin, 'pin%sy' % corner, "parent().par.%sy" % par)
setp(pin, 'extend', 'zero')
for n in ('bgcolorr', 'bgcolorg', 'bgcolorb'): setp(pin, n, 0)
setp(pin, 'bgcolora', 1)
ofx = glsl(SH, 'outfix', 'outfix.glsl', 200, -200, ['uO0'], (pin,), 'rgba8fixed')
final = mk(SH, nullTOP, 'final', 400, -200, (ofx,))

# ─────────────── previz: obraz promítnutý do záběru kamery / fotky místa ───────────────
pimg = mk(SH, moviefileinTOP, 'prev_photo', -1400, -1250); expr(pimg, 'file', "parent().par.Previzimage")
pbg = mk(SH, switchTOP, 'prev_bg', -1200, -1150, (cam, pimg)); expr(pbg, 'index', "1 if parent().par.Previzimage else 0")
pfit = mk(SH, fitTOP, 'prev_fit', -1000, -1150, (pbg,)); res(pfit)
pdim = mk(SH, levelTOP, 'prev_dim', -800, -1150, (pfit,)); expr(pdim, 'opacity', "1"); expr(pdim, 'brightness1', "1 - parent().par.Prevdim")
ppin = mk(SH, cornerpinTOP, 'prev_pin', -800, -1300, (ms,))
for corner, par in (('topleft', 'Prevtl'), ('topright', 'Prevtr'), ('botleft', 'Prevbl'), ('botright', 'Prevbr')):
	setp(ppin, 'pin%sunit' % corner, 'fraction')
	expr(ppin, 'pin%sx' % corner, "parent().par.%sx" % par); expr(ppin, 'pin%sy' % corner, "parent().par.%sy" % par)
setp(ppin, 'extend', 'zero')
pglow = mk(SH, blurTOP, 'prev_glow', -600, -1300, (ppin,)); setp(pglow, 'size', 6)
padd = mk(SH, compositeTOP, 'prev_add', -400, -1200, (pdim, ppin, pglow)); setp(padd, 'operand', 'add')
pv = mk(SH, switchTOP, 'previz', -200, -1200, (pfit, padd)); expr(pv, 'index', "1 if parent().par.Previz else 0")

# ─────────────── ovládací okno (UI) ───────────────
camtxt = mk(SH, textTOP, 'ui_camoff', 600, -900)
setp(camtxt, 'text', 'KAMERA VYPNUTÁ\n\nzapni: Camera → Kamera zapnutá\n(iPhone přes Continuity Camera nebo webkamera)\n\nPreviz = vizuál promítnutý do záběru kamery / fotky místa')
res(camtxt); setp(camtxt, 'fontsizex', 30)
for n, v in (('fontcolorr', .5), ('fontcolorg', .55), ('fontcolorb', .6), ('bgalpha', 1)): setp(camtxt, n, v)
pvui = mk(SH, switchTOP, 'ui_prev', 800, -900, (camtxt, pv)); expr(pvui, 'index', "1 if (parent().par.Camera or parent().par.Previz) else 0")
mt = glsl(SH, 'ui_meters', 'meters.glsl', 600, -600, ['uA0', 'uA1', 'uA2'], fmt='rgba8fixed')
setp(mt, 'outputresolution', 'custom'); mt.par.resolutionw.expr = ''; mt.par.resolutionh.expr = ''
mt.par.resolutionw = 480; mt.par.resolutionh = 120
itx = mk(SH, textTOP, 'ui_info', 600, -750); itx.par.dat = info; setp(itx, 'text', '')
setp(itx, 'outputresolution', 'custom'); setp(itx, 'resolutionw', 1000); setp(itx, 'resolutionh', 170)
setp(itx, 'font', 'Menlo'); setp(itx, 'fontsizex', 17); setp(itx, 'alignx', 'left'); setp(itx, 'aligny', 'top')
setp(itx, 'positionx', 14); setp(itx, 'positiony', -10)
for n, v in (('bgcolorr', .05), ('bgcolorg', .05), ('bgcolorb', .07), ('bgalpha', 1)): setp(itx, n, v)
UIW, UIH = 1440, 860                                   # vejde se i na displej MacBooku Air
ui = mk(SH, containerCOMP, 'ui', 800, -600)
setp(ui, 'w', UIW); setp(ui, 'h', UIH); setp(ui, 'bgcolorr', .02); setp(ui, 'bgcolorg', .02); setp(ui, 'bgcolorb', .03); setp(ui, 'bgalpha', 1)
def panel(name, top, x, y, w, h):
	c = ui.create(containerCOMP, name)
	setp(c, 'x', x); setp(c, 'y', y); setp(c, 'w', w); setp(c, 'h', h); c.par.top = top
	return c
PVW = (UIW - 30) // 2; PVH = PVW * 9 // 16
panel('p_out', final, 10, UIH - 10 - PVH, PVW, PVH)
panel('p_prev', pvui, 20 + PVW, UIH - 10 - PVH, PVW, PVH)
panel('p_info', itx, 10, UIH - 20 - PVH - 170, UIW - 500, 170)
panel('p_meters', mt, UIW - 480, UIH - 20 - PVH - 170, 470, 170)
pc = ui.create(parameterCOMP, 'p_pars')
setp(pc, 'x', 10); setp(pc, 'y', 10); setp(pc, 'w', UIW - 20); setp(pc, 'h', UIH - 40 - PVH - 170)
pc.par.op = SH.path; setp(pc, 'builtin', False); setp(pc, 'custom', True); setp(pc, 'header', False); setp(pc, 'pagenames', True)

# ─────────────── okna ───────────────
pw = mk(SH, windowCOMP, 'projector', 600, -200)
pw.par.winop = final.path
for n, v in (('borders', False), ('size', 'fill'), ('justifyoffsetto', 'specifydisplay'), ('cursorvisible', False), ('title', 'DJ SHOW – projektor'), ('closeescape', True)): setp(pw, n, v)
cw = mk(SH, windowCOMP, 'control', 1000, -600)
cw.par.winop = ui.path
for n, v in (('borders', True), ('size', 'custom'), ('winw', UIW), ('winh', UIH), ('title', 'DJ SHOW – ovládání'), ('justifyoffsetto', 'primarydisplay')): setp(cw, n, v)
setp(op('/perform'), 'winop', ui.path)
SH.par.opviewer = final.path

print('DJ SHOW postaveno.' + (' Upozornění:' if LOG else ' Bez upozornění.'))
for l in LOG: print('  -', l)
