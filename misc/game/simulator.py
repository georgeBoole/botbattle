from settlers import Tile, Adjacency, TileEdge, TileVertex
from constants import *
from bulbs.neo4jserver import Graph, Config
import os, random, itertools
from collections import defaultdict, Iterable

config = Config('http://192.168.1.14:7474/db/data/')
g = Graph(config)

g.add_proxy('tiles', Tile)
g.add_proxy('touches', Adjacency)
g.add_proxy('sides', TileEdge)
g.add_proxy('corners', TileVertex)


def configure_model():
	vertex_dict = defaultdict(lambda: defaultdict(dict))
	edge_dict = defaultdict(dict)

	def mk_ti(**kwargs):
		return g.tiles.create(**kwargs)
	def mk_to(src, dst):
		return g.touches.create(src, 'touches', dst)
	def mk_s(src, dst, **data):
		h, t = sorted([src, dst], key=lambda x: x._id if hasattr(x, '_id') else 0)
		if not t in edge_dict[h]:
			edge_dict[h][t] = g.sides.create(src, dst, **data)
		return edge_dict[h][t]
	def mk_c(x,y,v):
		coords = v_coords(x,y,v)
		vert = None
		for c in coords:
			if v in vertex_dict[x][y]:
				vert = vertex_dict[x][y][v]
				oc = filter(lambda q: q != c and not vert in vertex_dict[q[0]][q[1]], coords)
				for ox, oy in oc:
					vertex_dict[ox][oy] = vert
				break
		if not vert:
			vert = g.corners.create()
		return vert


	return mk_ti, mk_s, mk_c, mk_to, g

tiles, side, corner, touch, graph = configure_model()

vertices = (a, b, c, d, e, f) = range(6)
neighbor_coords = [(0,-1),(1,-1),(1,0),(0,1),(-1,1),(-1,0)]
def v_coords(x, y, v):
	n, ne, se, s, sw, nw = [ (x + nx, y + ny) for nx, ny in neighbor_coords ]
	co = lambda c,v: c + (v,)
	e_coords = None
	if v == a:
	    e_coords = co(nw, c), co(n, e)
	elif v == b:
	    e_coords =  co(n, d), co(ne, f)
	elif v == c:
	    e_coords =  co(ne, e), co(se, a)
	elif v == d:
	    e_coords =  co(se, f), co(s, b)
	elif v == e:
	    e_coords =  co(s, a), co(sw, c)
	elif v == f:
	    e_coords =  co(sw, b), co(nw, d)
	return ((x,y,v),) + e_coords if e_coords else ((x,y,v),)


def v_tiles(x, y, v):
	xy_values = [ (x, y) for x,y,v in v_coords(x,y,v) ]
	res = list()
	for til in graph.tiles.get_all():
		if (til.x, til.y) in xy_values:
			res.append(til)
	return res


def build_map():
	# just hold onto the center tile and its fine
	kinds = resources + (DESERT,)
	all_tiles = [ [r] * TILE_QUANTITY[r] for r in kinds ]
	print 'kinds: %s, tiles: %s' % (kinds, all_tiles)
	board_tiles = reduce(lambda a,b: a + b, all_tiles)
	production_tiles = list(PRODUCTION_NUMBERS)
	random.shuffle(board_tiles)
	random.shuffle(production_tiles)
	def gtt():
		return board_tiles.pop()
	def gpn():
		return production_tiles.pop()
	def gtc():
		tt = gtt()
		if tt is DESERT:
			return tt, 0
		else:
			return tt, gpn()
	bld_map(2,1, gtc, list(resource_tile_coords))

tile_map = defaultdict(dict)
def bld_map(x,y,get_tile_config,rem_tiles):
	if not (x,y) in rem_tiles:
		return
	tt, pn = get_tile_config()
	new_tile = graph.tiles.create(tile_type=tt, production_number=pn, x=x, y=y)
	tile_map[x][y] = new_tile
	rem_tiles.remove((x,y))
	adjacent_coords = filter(lambda ac: ac in rem_tiles, [(x+ax, y+ay) for ax,ay in acm])
	adj_tiles = [bld_map(nx, ny, get_tile_config, rem_tiles) for nx,ny in  adjacent_coords ]
	for at in adj_tiles:
		touch(new_tile, at)
	for nx, ny in filter(lambda m: m in resource_tile_coords and not m in adjacent_coords, [(x+ax, y+ay) for ax,ay in acm]):
		touch(new_tile, tile_map[nx][ny])



	prev_corn = None

	for x,y,v in [ (x,y,vertex) for vertex in vertices ]:
		my_vtx = corner(x,y,v)
		if prev_corn:
			side(prev_corn, my_vtx)
		tiles = v_tiles(x,y,v)
		for t in tiles:
			print 
			touch(my_vtx, t)
	return new_tile

def main():
	build_map()
	graph_ml = graph.get_graphml()
	with open('output.gml', 'w') as gml_file:
		gml_file.write(graph_ml)
	print 'done'

if __name__ == '__main__':
	main()