#!/usr/bin/env python3
"""Vyřízne z 3D modelů části těla pro scénu Membrána a uloží je jako samostatné OBJ v show/assets.

Zdroje (show/assets/src):
  makehuman_base.obj  — MakeHuman base mesh, CC0 (github.com/makehumancommunity/makehuman)
  LeePerrySmith.glb   — „Infinite, 3D Head Scan“ Lee Perry-Smith, CC BY 3.0 (z repozitáře three.js)

Výstup: hand.obj, foot.obj, face.obj — vycentrované, délka dílu = 1, osa délky = +Y (prsty / špička nahoru),
        přední strana (dlaň / chodidlo / obličej) míří k +Z, tedy proti plátnu.
Spuštění:  python3 show/src/tools/make_body_parts.py
"""
import json, math, os, struct

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, '..', '..', 'assets'))
SRC = os.path.join(ASSETS, 'src')


def load_obj_groups(path):
	V, faces, G = [], {}, None
	for line in open(path, encoding='utf-8'):
		if line.startswith('v '):
			V.append(tuple(map(float, line.split()[1:4])))
		elif line.startswith('g '):
			G = line.split()[1]
		elif line.startswith('f '):
			faces.setdefault(G, []).append([int(t.split('/')[0]) - 1 for t in line.split()[1:]])
	return V, faces


def centroid(V, faces):
	idx = {i for f in faces for i in f}
	n = len(idx)
	return tuple(sum(V[i][k] for i in idx) / n for k in range(3))


def sub(a, b): return tuple(x - y for x, y in zip(a, b))
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def norm(a):
	l = math.sqrt(dot(a, a)) or 1.0
	return tuple(x / l for x in a)


def cut_part(V, body, base, tip, front_hint, back=.12, radius=.75):
	"""díl = body těla za kloubem `base` směrem ke `tip`; vrací (vrcholy, plochy) v lokálních souřadnicích"""
	axis = sub(tip, base)
	L = math.sqrt(dot(axis, axis)); ay = norm(axis)
	az = norm(sub(front_hint, tuple(dot(front_hint, ay) * c for c in ay)))   # přední strana kolmo na délku
	ax = cross(ay, az)
	keep = set()
	for i in {i for f in body for i in f}:
		d = sub(V[i], base)
		t = dot(d, ay) / L
		r = math.sqrt(max(0.0, dot(d, d) - dot(d, ay) ** 2)) / L
		if -back <= t <= 1.25 and r <= radius:
			keep.add(i)
	F = [f for f in body if all(i in keep for i in f)]
	used = sorted({i for f in F for i in f})
	remap = {old: new for new, old in enumerate(used)}
	mid = tuple(b + a * .5 for b, a in zip(base, sub(tip, base)))
	P = []
	for i in used:
		d = sub(V[i], mid)
		P.append((dot(d, ax) / L, dot(d, ay) / L, dot(d, az) / L))
	return P, [[remap[i] for i in f] for f in F]


def load_glb(path):
	b = open(path, 'rb').read()
	jl = struct.unpack('<I', b[12:16])[0]
	J = json.loads(b[20:20 + jl])
	bin0 = 20 + jl + 8
	def acc(i):
		a = J['accessors'][i]; bv = J['bufferViews'][a['bufferView']]
		off = bin0 + bv.get('byteOffset', 0) + a.get('byteOffset', 0)
		comps = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}[a['type']]
		fmt = {5123: 'H', 5125: 'I', 5126: 'f'}[a['componentType']]
		size = struct.calcsize(fmt)
		stride = bv.get('byteStride', size * comps)
		return [struct.unpack_from('<%d%s' % (comps, fmt), b, off + k * stride) for k in range(a['count'])]
	prim = J['meshes'][0]['primitives'][0]
	P = [tuple(p) for p in acc(prim['attributes']['POSITION'])]
	I = [i[0] for i in acc(prim['indices'])]
	return P, [I[k:k + 3] for k in range(0, len(I), 3)]


def write_obj(path, P, F, note):
	with open(path, 'w', encoding='utf-8') as f:
		f.write('# %s\n' % note)
		for p in P: f.write('v %.5f %.5f %.5f\n' % p)
		for t in F: f.write('f ' + ' '.join(str(i + 1) for i in t) + '\n')
	print('%-9s %6d vrcholů %6d ploch  →  %s' % (os.path.basename(path), len(P), len(F), path))


def main():
	V, groups = load_obj_groups(os.path.join(SRC, 'makehuman_base.obj'))
	body = groups['body']
	J = lambda g: centroid(V, groups[g])
	# pravá ruka postavy = kladné x; dlaň v A-póze míří k tělu (−x) → přední strana dílu = dlaň
	wrist, tip = J('joint-r-hand'), J('joint-r-finger-3-4')
	if wrist[0] < 0: wrist, tip = J('joint-l-hand'), J('joint-l-finger-3-4')
	hand = cut_part(V, body, wrist, tip, front_hint=(-1.0, 0.0, 0.0), back=.15, radius=.8)
	write_obj(os.path.join(ASSETS, 'hand.obj'), *hand, note='ruka z MakeHuman base mesh (CC0)')
	# chodidlo: od kotníku ke konečku palce, „přední strana“ = chodidlo (dolů, −y)
	ankle, toe = J('joint-r-ankle'), J('joint-r-toe-1-3')
	if ankle[0] < 0: ankle, toe = J('joint-l-ankle'), J('joint-l-toe-1-3')
	foot = cut_part(V, body, ankle, toe, front_hint=(0.0, -1.0, 0.0), back=.35, radius=.75)
	write_obj(os.path.join(ASSETS, 'foot.obj'), *foot, note='chodidlo z MakeHuman base mesh (CC0)')
	# obličej: celý sken hlavy, normovaný na výšku 1, obličej k +Z
	P, F = load_glb(os.path.join(SRC, 'LeePerrySmith.glb'))
	ys = [p[1] for p in P]; h = max(ys) - min(ys)
	c = tuple(sum(p[k] for p in P) / len(P) for k in range(3))
	P = [((p[0] - c[0]) / h, (p[1] - c[1]) / h, (p[2] - c[2]) / h) for p in P]
	write_obj(os.path.join(ASSETS, 'face.obj'), P, F, note='Infinite, 3D Head Scan by Lee Perry-Smith, CC BY 3.0 (www.triplegangers.com)')


if __name__ == '__main__':
	main()
