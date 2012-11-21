import random as rnd
from neomodel import StructuredNode, StringProperty, IntegerProperty, BooleanProperty, RelationshipTo, RelationshipFrom, Relationship, OneOrMore, ZeroOrOne, One, ZeroOrMore
from Constants import *
from collections import Iterable, namedtuple, defaultdict
from itertools import permutations
from py2neo.neo4j import Direction
EITHER = Direction.EITHER
from clear_db import wipe
import json
    
class BoardElement(StructuredNode):
    occupation = RelationshipFrom('Piece', 'OCCUPATION', cardinality=ZeroOrMore)
    tiles = RelationshipTo('Tile', 'NEIGHBOR_TILES', cardinality=ZeroOrMore)
    vertices = RelationshipTo('Vertex', 'NEIGHBOR_VERTICES', cardinality=ZeroOrMore)
    edges = RelationshipTo('Edge', 'NEIGHBOR_EDGES', cardinality=ZeroOrMore)
    
class Tile(BoardElement):
    TILES = 6
    VERTICES = 6
    EDGES = 6
    tile_id = IntegerProperty(unique_index=True)
    tile_type = StringProperty(default=WATER)
    production_number = IntegerProperty(index=True, default=0)
    x = IntegerProperty(index=True, required=True)
    y = IntegerProperty(index=True, required=True)



class Edge(BoardElement):
    edge_id = IntegerProperty(unique_index=True)
    TILES = 2
    VERTICES = 2
    EDGES = 0
    
class Vertex(BoardElement):
    vertex_id = IntegerProperty(unique_index=True)
    TILES = 3
    VERTICES = 0
    EDGES = 3

class Piece(StructuredNode):
    piece_type = StringProperty(required=True)
    owner = RelationshipTo('PlayerState', 'OWNS',cardinality=ZeroOrOne)
    location = RelationshipTo(['Vertex', 'Edge', 'Tile'], 'LOCATION', cardinality=One)
    state = StringProperty(default='INACTIVE')

class GameState(StructuredNode):
    player_states = RelationshipTo('PlayerState', 'PLAYERS', cardinality=OneOrMore)
    turn_index = IntegerProperty(required=True)
    phase = StringProperty()
    status = StringProperty()
    status_idx = IntegerProperty(default=0)
    active_player = RelationshipTo('PlayerState', 'ACTIVE_PLAYER', cardinality=ZeroOrOne)

class Card(StructuredNode):
    card_type = StringProperty(required=True)
    card_name = StringProperty(required=True)
    face_up = BooleanProperty(default=False)
    owner = RelationshipTo('PlayerState', 'OWNS', cardinality=One)

no_rsc = lambda: IntegerProperty(default=0)

class PlayerState(StructuredNode):
    pid = IntegerProperty(required=True)
    name = StringProperty()
    wheat = no_rsc()
    brick = no_rsc()
    ore = no_rsc()
    wood = no_rsc()
    sheep = no_rsc()
    cards = RelationshipFrom('Card', 'OWNS', cardinality=ZeroOrMore)
    pieces = RelationshipFrom('Piece', 'OWNS', cardinality=ZeroOrMore)
    im_active = RelationshipFrom('GameState', 'ACTIVE_PLAYER', cardinality=ZeroOrOne)
    




vertices = (a, b, c, d, e, f) = range(6)
def equiv_coords(x, y, v):
    n, ne, se, s, sw, nw = [ (x + nx, y + ny) for nx, ny in neighbor_coords ]
    vertices = (a, b, c, d, e, f) = range(6)
    co = lambda c, v: c + (v,)
    if v == a:
        return co(nw, c), co(n, e)
    elif v == b:
        return co(n, d), co(ne, f)
    elif v == c:
        return co(ne, e), co(se, a)
    elif v == d:
        return co(se, f), co(s, b)
    elif v == e:
        return co(s, a), co(sw, c)
    elif v == f:
        return co(sw, b), co(nw, d)
    else:
        return None


def conn(rel, dst):
    if not rel or not dst:
        return
    itr = lambda x: isinstance(x, Iterable)
    if itr(rel):
        [ conn(r, dst) for r in rel ]
    if itr(dst):
        [ conn(rel, d) for d in dst ]

    src = rel
    dest = dst

    print 'testing if %s is connected to %s. types are %s and %s' % (rel, dst, type(rel), type(dst))
    if type(dest) == list and dest:
        dest = dest.pop()

    if not rel.is_connected(dest):
        print 'two components are not yet connected, connecting them'
        rel.connect(dest)
        rel.origin.save()



def build_board():
    tile_ids, edge_ids, vertex_ids = set(), set(), set()
    tile_label_list_list = [ [rsc] * TILE_QUANTITY[rsc] for rsc in filter(lambda x: x != WATER, tile_types) ]
    tile_label_list = list()
    for tll in tile_label_list_list:
    	if tll and isinstance(tll, Iterable):
    		tile_label_list.extend(tll)
    rnd.shuffle(tile_label_list)
    
    prod_nums = list(PRODUCTION_NUMBERS)
    rnd.shuffle(prod_nums)
    #print tile_label_list

    # create all the tiles
    for tx, ty in resource_tile_coords:
    	ttype = tile_label_list.pop()
    	tprod = prod_nums.pop() if not ttype == DESERT else 0
        new_tile = Tile(x=tx, y=ty, tile_type=ttype, production_number=tprod).save()
        tile_ids.add(new_tile.get_property())


    
    vertex_record = defaultdict(lambda: defaultdict(dict))

    def build_vertices(coord_list):
        total_built = 0
        for x,y,v in coord_list:
            fresh_one = build_vertex(x,y,v)
            if fresh_one:
                #print 'making a fresh vertex for %d, %d, %d' % (x,y,v)
                total_built += 1
        return total_built

    def build_vertex(tx, ty, vi):
        equivalent_coords = equiv_coords(tx, ty, vi)
        built_one = False
        coords = ((tx,ty,vi),) + equivalent_coords if equivalent_coords else ((tx, ty, vi),)
        found_vertex = None
        for x,y,v in coords:
            if v in vertex_record[x][y]:
                found_vertex = vertex_record[x][y][v]
                break
        if not found_vertex:
            found_vertex = Vertex().save()
            vertex_ids.add(found_vertex.vertex_id)


            built_one = True
            tiles = reduce(lambda a,b: a + b, [ Tile.index.search(x=cx, y=cy) for cx, cy, v in coords ])
            #print 'Tiles for vertex found: %s' % tiles
            for nt in tiles:
                #found_vertex.tiles.connect(nt)
                conn(found_vertex.tiles, nt)
            perms = permutations(tiles, 2)
            for p in perms:
                print p
                t1, t2 = p
                neighbor_edge = set(t1.edges.all()).intersection(set(t2.edges.all()))
                if isinstance(neighbor_edge, Iterable) and neighbor_edge and not type(neighbor_edge) == str:
                    neighbor_edge = neighbor_edge.pop()
                conn(found_vertex.edges, neighbor_edge)




        for x,y,v in coords:
            if not found_vertex in vertex_record[x][y]:
                vertex_record[x][y][v] = found_vertex
        return built_one


    matchup_record = dict()
    # wire up connections
    for tx, ty in resource_tile_coords:
        t = Tile.index.search(x=tx, y=ty).pop() if Tile.index.search(x=tx, y=ty) else None
        if not t:
            continue
        tid = t.tile_id
        rnc = [ (t.x + nc[0], t.y + nc[1]) for nc in neighbor_coords ]
        for nx, ny in rnc:
            res = Tile.index.search(x=nx, y=ny)
            n = res.pop() if res else None
            if n:
                nid = n.tile_id
                sids = tuple(sorted([tid, nid]))
                if sids in matchup_record:
                    continue
                else:
                    conn(t.tiles, n)#t.tiles.connect(n)
                    new_edge = Edge().save()
                    edge_ids.add(new_edge.edge_id)
                    conn(new_edge.tiles, t)#new_edge.tiles.connect(t)
                    conn(new_edge.tiles, n)#new_edge.tiles.connect(n)
                    new_edge.save()
                    conn(t.edges, new_edge)#t.edges.connect(new_edge)
                    t.save()
                    conn(n.edges, new_edge)#n.edges.connect(new_edge)
                    n.save()
                    matchup_record[sids] = new_edge

    v_coords = list()
    for x,y in resource_tile_coords:
        for vi in vertices:
            v_coords.append((x,y,vi))
    num_vertices = build_vertices(v_coords)
    #print 'made a total of %d vertices for the map' % num_vertices
    return [ tuple(w) for w in (tile_ids, edge_ids, vertex_ids) ]




player_names = ['Jace', 'Tezzeret', 'Chandra']
NUM_PLAYERS = len(player_names)

def examine_board():
    pass


def test_model():
    #players = [ PlayerState(pid=pid, name=pname).save() for pid, pname in enumerate(player_names) ]
    #a_road = Piece(piece_type='ROAD', owner=rnd.choice(players), state='Active').save()
    #tile_index = Tile.index
    #print dir(tile_index)
    #print tile_index.get()
    wipe()
    id_map = {'t':list(), 'e':list(), 'v':list()}
    id_map['t'], id_map['e'], id_map['v'] = build_board()
    #print json.dumps(id_map)
    return id_map





if __name__ == '__main__':
    test_model()




