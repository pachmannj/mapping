# DJ SHOW — sestavení scén (spouští ho build.py; používá jeho pomocné funkce mk, setp, expr, glsl, res, uniforms …)
SHOWP = "op('/project1/show').par."
KN = 500                                                           # body tunelu Krasohledu: KN × KN
HN = 500                                                           # body Heat: HN × HN

def custom_res(o, w, h):
	setp(o, 'outputresolution', 'custom')
	o.par.resolutionw.expr = ''; o.par.resolutionh.expr = ''
	o.par.resolutionw = w; o.par.resolutionh = h

def black_bg(o):
	for n, v in (('bgcolorr', 0), ('bgcolorg', 0), ('bgcolorb', 0), ('bgcolora', 1)): setp(o, n, v)

def additive(m):
	for n, v in (('blending', True), ('srcblend', 'one'), ('destblend', 'one'), ('depthtest', False), ('depthwriting', False), ('cullface', 'neither')): setp(m, n, v)

def instmat(parent, name, pos, col, x, y):
	"""sdílený materiál: instance obdélníku čtou polohu a barvu z textur (src/glsl/inst_*.glsl)"""
	vd = textfile(parent, name + '_vert', GL + '/inst_vert.glsl', x - 200, y)
	pd = textfile(parent, name + '_pixel', GL + '/inst_pixel.glsl', x - 200, y - 120)
	m = mk(parent, glslMAT, name, x, y); m.par.vdat = vd; m.par.pdat = pd
	uniforms(m, ['uI0'])
	for n, v in (('vec0valuex', 2), ('vec0valuey', 1280), ('vec0valuez', 720)): setp(m, n, v)   # bezpečné výchozí hodnoty
	m.seq.sampler.numBlocks = 2
	setp(m, 'sampler0name', 'sPos'); m.par.sampler0top = pos
	setp(m, 'sampler1name', 'sCol'); m.par.sampler1top = col
	additive(m)
	return m

def instgeo(parent, name, mat, count, x, y):
	g = mk(parent, geometryCOMP, name, x, y)
	for c in list(g.children): c.destroy()
	r = g.create(rectangleSOP, 'quad'); r.par.sizex = 1; r.par.sizey = 1; r.render = r.display = True
	setp(g, 'instancing', True); setp(g, 'instancecountmode', 'manual'); setp(g, 'numinstances', count)
	g.par.material = mat
	return g

def bloom(parent, src, x, y, amount_expr):
	"""záře: rozmazaná kopie přičtená k obrazu"""
	bl = mk(parent, blurTOP, 'bloom_blur', x, y - 150, (src,)); setp(bl, 'size', 24)
	lv = mk(parent, levelTOP, 'bloom_lvl', x + 200, y - 150, (bl,)); expr(lv, 'brightness1', amount_expr)
	ad = mk(parent, compositeTOP, 'bloom_add', x + 400, y, (src, lv)); setp(ad, 'operand', 'add')
	return ad

def trails(parent, src, x, y, prefix='fb'):
	"""ozvěna obrazu: předchozí snímek se lehce přiblíží, zeslábne a složí s novým"""
	fb = mk(parent, feedbackTOP, prefix, x, y - 150, (src,))
	xf = mk(parent, transformTOP, prefix + '_xf', x + 200, y - 150, (fb,))
	lv = mk(parent, levelTOP, prefix + '_lvl', x + 400, y - 150, (xf,)); setp(lv, 'opacity', .8)
	cp = mk(parent, compositeTOP, prefix + '_comp', x + 600, y, (src, lv)); setp(cp, 'operand', 'maximum')   # maximum: stopy nikdy nepřetečou do bílé
	fb.par.top = cp
	return cp

# ───────────────────────── KRASOHLED 2.0 ─────────────────────────
def build_krasohled(SH):
	K = mk(SH, baseCOMP, 'krasohled', -1100, 0)
	N = KN
	tube = glsl(K, 'tube', 'krasohled_tube.glsl', -800, 0, ['uK0', 'uK1', 'uK2', 'uK3', 'uK4', 'uL0', 'uL1', 'uL2'], fmt='rgba32float')
	custom_res(tube, N, N); setp(tube, 'numcolorbufs', 2)
	col = mk(K, renderselectTOP, 'tube_col', -600, -100); col.par.top = tube; setp(col, 'bufferindex', 1); setp(col, 'format', 'rgba16float')
	m = instmat(K, 'mat', tube, col, -400, -250)
	instgeo(K, 'geo', m, N * N, -200, -250)
	cam = mk(K, cameraCOMP, 'cam', -200, -400); expr(cam, 'tz', SHOWP + "Klength * .5 + 3.5"); setp(cam, 'fov', 70); setp(cam, 'far', 100)
	rend = mk(K, renderTOP, 'render', 0, -250)
	rend.par.camera = cam.path; rend.par.geometry = 'geo'
	res(rend, 'rgba16float'); black_bg(rend)
	# kaskáda zrcadel z videa: 0°, 90°, 45°, 180°, 90° (3. a 5. se točí s hudbou), počet volí parametr Zrcadla
	sw = glsl(K, 'mirrors', 'krasohled_mirrors.glsl', 400, -250, ['uM0', 'uM1'], (rend,))
	base = mk(K, nullTOP, 'base', 1150, -250, (sw,))
	glow = bloom(K, base, 1300, -250, SHOWP + "Bloom * .7")
	mk(K, nullTOP, 'out1', 2300, -250, (trails(K, glow, 1800, -250),))

# ───────────────────────── VORTEX 2.0 (POPs) ─────────────────────────
def build_vortex(SH):
	V = mk(SH, baseCOMP, 'vortex', -1100, -150)
	wave = mk(V, selectCHOP, 'wave', -800, 200); wave.par.chop = SH.op('a_in').path
	geo = mk(V, geometryCOMP, 'geo', -400, 0)
	for c in list(geo.children): c.destroy()
	emit = mk(geo, choptoPOP, 'emit', -600, 0); emit.par.chop = wave.path
	setp(emit, 'surftype', 'points'); setp(emit, 'attrscope', 'P(0) P(1)')
	parts = mk(geo, particlePOP, 'particles', -400, 0, (emit,))
	for n, v in (('maxparticles', 200000), ('birthrate', 50000), ('life', 5), ('lifevariance', .4), ('rndinputpts', True),
	             ('jitterbirthpos', True), ('createpointprim', True), ('damping', 0), ('initvelocityx', 0), ('initvelocityy', 0), ('initvelocityz', 0)):
		setp(parts, n, v)
	fd = textfile(geo, 'forces_dat', GL + '/vortex_forces.glsl', -200, -150)
	f = mk(geo, glslPOP, 'forces', -200, 0, (parts,))
	f.par.computedat = fd
	# Color a PointScale vznikají v Particle POP při zrodu částice; GLSL POP je jen přepisuje (druhá deklarace = chyba kompilace)
	parts.seq.attr.numBlocks = 2
	setp(parts, 'attr0name', 'color'); setp(parts, 'attr1name', 'pointscale')
	setp(f, 'outputattrs', 'PartVel Color PointScale')
	uniforms(f, ['uS%d' % i for i in range(11)] + ['uL0', 'uL1', 'uL2'])
	for i in range(14): setp(f, 'vec%dtype' % i, 'vec4')
	cull = mk(geo, deletePOP, 'cull', 0, 0, (f,))                     # z videa: Delete POP za poloměrem
	setp(cull, 'invert', 'keep'); cull.seq.bound.numBlocks = 1
	for n, v in (('bound0enabled', True), ('bound0type', 'boundingsphere'), ('bound0scalex', 7), ('bound0scaley', 7), ('bound0scalez', 7)): setp(cull, n, v)
	out = mk(geo, nullPOP, 'out', 200, 0, (cull,)); out.display = out.render = True
	parts.par.targetpop = out
	mat = mk(geo, pointspriteMAT, 'mat', 200, -200)
	setp(mat, 'pointscaleattrib', 'PointScale'); expr(mat, 'pointsize', SHOWP + "Vsize")
	additive(mat)
	geo.par.material = mat
	org = mk(V, nullCOMP, 'origin', -400, -200)
	cam = mk(V, cameraCOMP, 'cam', -400, -350)
	setp(cam, 'viewanglemethod', 'vertfov'); setp(cam, 'fov', 60.16); setp(cam, 'near', .1); setp(cam, 'far', 100); cam.par.lookat = org; cam.par.tz = 4
	rend = mk(V, renderTOP, 'render', -200, -200)
	rend.par.camera = cam.path; rend.par.geometry = 'geo'
	res(rend, 'rgba16float'); black_bg(rend)
	tr = trails(V, rend, 0, -200)
	glow = bloom(V, tr, 800, -200, "1")
	co = glsl(V, 'compose', 'vortex_compose.glsl', 1400, -200, ['uC0'], (glow,))
	mk(V, nullTOP, 'out1', 1600, -200, (co,))
	setp(parts, 'play', False)                                         # simulaci spouští až sc_vortex, když je scéna aktivní

# ───────────────────────── ECHOES 2.0 ─────────────────────────
def build_echoes(SH):
	E = mk(SH, baseCOMP, 'echoes', -1100, -300)
	field = glsl(E, 'field', 'echoes_field.glsl', -800, 0, ['uE0', 'uE1', 'uE2'] + ['uR%d' % i for i in range(8)] + ['uL0', 'uL1', 'uL2', 'uE3'])
	prev = field
	for i in range(5):                                               # z videa: 5× Edge TOP, alfa = 1
		prev = mk(E, edgeTOP, 'edge%d' % (i + 1), -600 + i * 130, 0, (prev,)); setp(prev, 'alphaoutputmenu', 'one')
	fb1 = trails(E, prev, 100, 0, 'fb1')                              # feedback: jas 0,9 + add
	E.op('fb1_xf').bypass = True; setp(E.op('fb1_lvl'), 'opacity', 1)
	lim = mk(E, limitTOP, 'limit', 800, 0, (fb1,)); setp(lim, 'quantpos', 'round'); setp(lim, 'posstep', .03)
	dis = mk(E, displaceTOP, 'displace', 950, 0, (fb1, lim))
	e6 = mk(E, edgeTOP, 'edge6', 1100, 0, (dis,)); setp(e6, 'alphaoutputmenu', 'one')
	fb2 = trails(E, e6, 1250, 0, 'fb2')                               # druhá ozvěna se zoomem 0,99
	lv = mk(E, levelTOP, 'out_lvl', 1950, 0, (fb2,)); setp(lv, 'contrast', 1.3); setp(lv, 'inlow', .1)
	mk(E, nullTOP, 'out1', 2100, 0, (lv,))

# ───────────────────────── HEAT 2.0 ─────────────────────────
def build_heat(SH):
	H = mk(SH, baseCOMP, 'heat', -1100, -450)
	N = HN
	start = glsl(H, 'start', 'heat_start.glsl', -800, 200, ['uH0'], fmt='rgba32float'); custom_res(start, N, N)
	zero = mk(H, constantTOP, 'zero', -800, 0)
	custom_res(zero, N, N); setp(zero, 'format', 'rgba32float')
	for n in ('colorr', 'colorg', 'colorb', 'alpha'): setp(zero, n, 0)
	fb = mk(H, feedbackTOP, 'state', -600, 0, (zero,))
	sim = glsl(H, 'sim', 'heat_sim.glsl', -400, 0, ['uH0', 'uH1', 'uH2', 'uH3', 'uR0', 'uR1', 'uR2', 'uR3', 'uL0', 'uL1', 'uL2', 'uH4'], (fb, start), 'rgba32float')
	setp(sim, 'numcolorbufs', 3)
	fb.par.top = sim
	pos = mk(H, renderselectTOP, 'pos', -200, 50); pos.par.top = sim; setp(pos, 'bufferindex', 1); setp(pos, 'format', 'rgba32float')
	col = mk(H, renderselectTOP, 'col', -200, -50); col.par.top = sim; setp(col, 'bufferindex', 2); setp(col, 'format', 'rgba16float')
	m = instmat(H, 'mat', pos, col, 0, -200)
	instgeo(H, 'geo', m, N * N, 200, -200)
	cam = mk(H, cameraCOMP, 'cam', 200, -350); setp(cam, 'projection', 'ortho'); setp(cam, 'orthowidth', 2 * 16 / 9); cam.par.tz = 5
	rend = mk(H, renderTOP, 'render', 400, -200)
	rend.par.camera = cam.path; rend.par.geometry = 'geo'
	res(rend, 'rgba16float'); black_bg(rend)
	glow = bloom(H, rend, 600, -200, "1")
	mk(H, nullTOP, 'out1', 1200, -200, (glow,))


# ───────────────────────── PTÁK ─────────────────────────
def build_bird(SH):
	Bc = mk(SH, baseCOMP, 'bird', -1100, -600)
	vid = mk(Bc, moviefileinTOP, 'video', -900, 0)
	vid.par.file = 'media/seagull_45246.mp4'                         # relativně ke složce show
	setp(vid, 'playmode', 'sequential'); setp(vid, 'play', True); setp(vid, 'interp', True)
	setp(vid, 'loopcrossfadeunit', 'seconds'); setp(vid, 'loopcrossfade', 1.5)      # konec smyčky se prolne se začátkem
	key = glsl(Bc, 'key', 'bird_key.glsl', -700, 0, ['uK0'], (vid,))
	for n, v in (('vec0valuex', .05), ('vec0valuey', .15), ('vec0valuez', 1)): setp(key, n, v)
	small = mk(Bc, resolutionTOP, 'mask_small', -700, -200, (key,)); custom_res(small, 64, 36)
	flap = glsl(Bc, 'flap', 'bird_flap.glsl', -500, 0, ['uF0', 'uF1'], (key,))
	for n, v in (('vec0valuex', .5), ('vec0valuey', .5), ('vec0valuez', 1), ('vec1valuey', .05), ('vec1valuez', .3), ('vec1valuew', 1.78)): setp(flap, n, v)
	PW, PH = 480, 270                                                  # 130 tisíc částic = pixely ptáka
	zero = mk(Bc, constantTOP, 'zero', -500, -300); custom_res(zero, PW, PH); setp(zero, 'format', 'rgba32float')
	for n in ('colorr', 'colorg', 'colorb', 'alpha'): setp(zero, n, 0)
	fb = mk(Bc, feedbackTOP, 'state', -300, -300, (zero,))
	parts = glsl(Bc, 'parts', 'bird_parts.glsl', -100, -300, ['uP0', 'uP1', 'uP2'], (fb, flap), 'rgba32float')
	setp(parts, 'numcolorbufs', 3); fb.par.top = parts
	for n, v in (('vec0valuew', 3.5), ('vec1valuew', 1.78)): setp(parts, n, v)
	pos = mk(Bc, renderselectTOP, 'pos', 100, -250); pos.par.top = parts; setp(pos, 'bufferindex', 1); setp(pos, 'format', 'rgba32float')
	col = mk(Bc, renderselectTOP, 'col', 100, -350); col.par.top = parts; setp(col, 'bufferindex', 2); setp(col, 'format', 'rgba16float')
	m = instmat(Bc, 'mat', pos, col, 300, -450)
	instgeo(Bc, 'geo', m, PW * PH, 500, -450)
	cam = mk(Bc, cameraCOMP, 'cam', 500, -600); setp(cam, 'projection', 'ortho'); setp(cam, 'orthowidth', 2 * 16 / 9); cam.par.tz = 5
	rend = mk(Bc, renderTOP, 'render', 700, -400)
	rend.par.camera = cam.path; rend.par.geometry = 'geo'
	res(rend, 'rgba16float'); black_bg(rend)
	photo = mk(Bc, levelTOP, 'photo_lvl', -300, 0, (flap,))
	mix = mk(Bc, compositeTOP, 'mix', 900, 0, (photo, rend)); setp(mix, 'operand', 'add')
	# ── historie snímků (60 snímků, 640×360) pro slit-scan a chronofotografii ──
	sway = mk(Bc, transformTOP, 'sway', -500, 400, (flap,)); setp(sway, 'extend', 'zero')   # houpání v rytmu: kopie v čase se rozestoupí
	hsrc = mk(Bc, resolutionTOP, 'hist_src', -300, 400, (sway,)); custom_res(hsrc, 640, 360); setp(hsrc, 'format', 'rgba8fixed')
	hist = mk(Bc, texture3dTOP, 'hist', -100, 400, (hsrc,)); setp(hist, 'cachesize', 60)
	tmap = glsl(Bc, 'tmap', 'bird_tmap.glsl', -100, 600, ['uT0', 'uT1'], fmt='rgba8fixed'); custom_res(tmap, 320, 180)
	for n_, v_ in (('vec0valuez', .5), ('vec0valuew', .5), ('vec1valuex', 1), ('vec1valuez', 1.78)): setp(tmap, n_, v_)
	slit = mk(Bc, timemachineTOP, 'slit', 100, 500, (hist, tmap))
	setp(slit, 'blackoffsetunit', 'frames'); setp(slit, 'whiteoffsetunit', 'frames'); setp(slit, 'blackoffset', 0); setp(slit, 'whiteoffset', 30)
	zmap = mk(Bc, constantTOP, 'zero_map', -100, 750); custom_res(zmap, 16, 9)
	for n_ in ('colorr', 'colorg', 'colorb'): setp(zmap, n_, 0)
	echoes = [hsrc]
	for i in range(1, 6):                                             # kopie ptáka z postupně starších okamžiků
		e_ = mk(Bc, timemachineTOP, 'echo%d' % i, 100 + i * 130, 750, (hist, zmap))
		setp(e_, 'blackoffsetunit', 'frames'); setp(e_, 'whiteoffsetunit', 'frames'); setp(e_, 'blackoffset', i * 6); setp(e_, 'whiteoffset', i * 6)
		echoes.append(e_)
	chrono = glsl(Bc, 'chrono', 'bird_chrono.glsl', 900, 700, ['uC0', 'uC1'], tuple(echoes))
	setp(chrono, 'vec0valuex', 1); setp(chrono, 'vec0valuey', .7)
	izero = mk(Bc, constantTOP, 'ink_zero', 300, 1000); custom_res(izero, 640, 360); setp(izero, 'format', 'rgba16float')
	for n_ in ('colorr', 'colorg', 'colorb'): setp(izero, n_, 0)
	ifb = mk(Bc, feedbackTOP, 'ink_fb', 500, 1000, (izero,))
	ink = glsl(Bc, 'ink', 'bird_ink.glsl', 700, 1000, ['uI0', 'uI1'], (ifb, flap))
	ifb.par.top = ink
	for n_, v_ in (('vec0valuez', .9), ('vec1valuez', 1.78), ('vec1valuew', 2)): setp(ink, n_, v_)
	look = glsl(Bc, 'look', 'bird_look.glsl', 1100, 300, ['uL0', 'uL1'], (mix, slit, chrono, ink), custom_res=True)
	setp(look, 'vec0valuex', 1); setp(look, 'vec1valuez', 1)
	ctr = mk(Bc, transformTOP, 'center', 1200, 450, (look,)); setp(ctr, 'extend', 'zero')     # pták doprostřed, ať se zrcadlí on, ne obloha
	fold = glsl(Bc, 'fold', 'krasohled_mirrors.glsl', 1300, 300, ['uM0', 'uM1'], (ctr,))   # kaleidoskop (stejný shader jako Krasohled)
	setp(fold, 'vec1valuez', 1.78); setp(fold, 'vec1valuey', 4)
	fmix = mk(Bc, crossTOP, 'fold_mix', 1450, 300, (look, fold))      # kaleidoskop se plynule prolne, neskočí
	tr = trails(Bc, fmix, 1600, 300)
	glow = bloom(Bc, tr, 2300, 300, "0.5")
	mk(Bc, nullTOP, 'out1', 2900, 300, (glow,))

# ───────────────────────── KVĚT (skutečná lilie) ─────────────────────────
def build_flower(SH):
	Fc = mk(SH, baseCOMP, 'flower', -1100, -750)
	src = mk(Fc, moviefileinTOP, 'frame_src', -800, 0); src.par.file = 'media/lily/f_01.jpg'
	ph = mk(Fc, texture3dTOP, 'phases', -600, 0, (src,))                # 64 fází rozkvětu; plní je sc_flower.preload()
	for n_, v_ in (('cachesize', 64), ('active', False), ('replacesingle', True)): setp(ph, n_, v_)
	lily = glsl(Fc, 'lily', 'lily.glsl', -400, 0, ['uB0', 'uB1', 'uB2', 'uB3', 'uL0', 'uL1', 'uL2'], (ph,), custom_res=True)
	for n_, v_ in (('vec0valuex', .3), ('vec1valuex', .5), ('vec1valuey', .63), ('vec1valuez', .32), ('vec1valuew', 6),
	               ('vec3valuex', 1), ('vec3valuez', 1), ('vec3valuew', 1.78)): setp(lily, n_, v_)   # bezpečné výchozí hodnoty
	fold = glsl(Fc, 'fold', 'krasohled_mirrors.glsl', -200, 150, ['uM0', 'uM1'], (lily,))
	setp(fold, 'vec1valuez', 1.78); setp(fold, 'vec1valuey', 3)
	fmix = mk(Fc, crossTOP, 'fold_mix', 0, 0, (lily, fold))
	tr = trails(Fc, fmix, 200, 0)
	glow = bloom(Fc, tr, 1000, 0, "0.6")
	mk(Fc, nullTOP, 'out1', 1600, 0, (glow,))
