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
	# Color a PointScale vytváří už Particle POP — vlastní deklarace by je zdvojila (chyba kompilace)
	setp(f, 'outputattrs', 'PartVel Color PointScale')
	uniforms(f, ['uS%d' % i for i in range(11)])
	for i in range(11): setp(f, 'vec%dtype' % i, 'vec4')
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
	field = glsl(E, 'field', 'echoes_field.glsl', -800, 0, ['uE0', 'uE1', 'uE2'] + ['uR%d' % i for i in range(8)])
	prev = field
	for i in range(5):                                               # z videa: 5× Edge TOP, alfa = 1
		prev = mk(E, edgeTOP, 'edge%d' % (i + 1), -600 + i * 130, 0, (prev,)); setp(prev, 'alphaoutputmenu', 'one')
	fb1 = trails(E, prev, 100, 0, 'fb1')                              # feedback: jas 0,9 + add
	E.op('fb1_xf').bypass = True; setp(E.op('fb1_lvl'), 'opacity', 1)
	lim = mk(E, limitTOP, 'limit', 800, 0, (fb1,)); setp(lim, 'quantpos', 'round'); setp(lim, 'posstep', .03)
	dis = mk(E, displaceTOP, 'displace', 950, 0, (fb1, lim))
	e6 = mk(E, edgeTOP, 'edge6', 1100, 0, (dis,)); setp(e6, 'alphaoutputmenu', 'one')
	fb2 = trails(E, e6, 1250, 0, 'fb2')                               # druhá ozvěna se zoomem 0,99
	lv = mk(E, levelTOP, 'out_lvl', 1950, 0, (fb2,)); setp(lv, 'contrast', 1.3); setp(lv, 'blacklevel', .12)
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
	sim = glsl(H, 'sim', 'heat_sim.glsl', -400, 0, ['uH0', 'uH1', 'uH2', 'uH3', 'uR0', 'uR1', 'uR2', 'uR3'], (fb, start), 'rgba32float')
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
