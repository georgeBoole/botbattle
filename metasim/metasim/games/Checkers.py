import random
from collections import namedtuple
from itertools import permutations

BOARD_SIZE = 8
DISCS_PER_PLAYER = 12
COLORS = (RED, BLACK) = ('Red', 'Black')
EMPTY, OCCUPIED = ('Empty', 'Occupied')
KING_LOC = {RED:BOARD_SIZE-1, BLACK:0}
SQUARE_STATES = (empty_red, empty_black, occupied_red, occupied_black) = ('=', '0', 'R', 'B')

Piece = namedtuple('Piece', ['color', 'x', 'y', 'is_king'])
Move = namedtuple('Move', ['piece', 'action', 'movement_path', 'pieces_removed', 'was_made_king'])
actions = (MOVE, JUMP)

def isodd(n):
	return n % 2 == 1

def color(x, y):
	return BLACK if isodd(x) == isodd(y) else RED

def game_over(grid, discs):
	pass

def valid_loc(r, t):
	return r in legal_coords and t in legal_coords

def dist(a, b):
	ax, ay = a
	bx, by = b
	return abs(ax-bx) + abs(ay-by)


normal_movements = [ (-1, -1), (-1, 1), (1, 1), (1, -1) ]
jump_movements = [ (-2,-2), (-2, 2), (2,2), (2,-2) ]
legal_coords = range(BOARD_SIZE)

def get_neighbors(x,y, distance=1, remove_invalid=True):
	all_coords = [ (x+(dx*distance),y+(dy*distance)) for dx,dy in normal_movements]
	return filter(lambda r,s: valid_loc(r,s), all_coords) if remove_invalid else all_coords


def can_jump(jumper_color, from, over, to, omap):
	if not valid_loc(to) or omap[to[0]][to[1]] != EMPTY:
		return False
	return jumper_color != omap[over[0]][over[1]].color and dist(from,over) == 2 and dist(over,to) == 2 and dist(from,to) == 4

def build_jump(piece, hops):
	s_hops = sorted(hops, key=lambda h: h[3])
	mpath = set(reduce(lambda l,r: l + r, [ (hp[0], hp[1]) for hp in s_hops ]))
	p_rem = [ hp[2] for hp in s_hops ]
	return Move(piece, JUMP, mpath, p_rem, mpath[-1] == KING_LOC[piece.color])


jump_tuple_fields = (source, dest, victim, stage) = ('jump source', 'jump dest', 'jump victim', 'jump stage')
# temporarily store jumps as (jump_source, jump_dest, jump_victim, jump_stage)
def try_jump(piece, target, jumper, occupancy_map):
	all_hops = _try_jump(piece.color, target, occupancy_map, 0)
	if not all_hops:
		return None
	# determine max stage and break down hops by stage
	max_stage = max([hp[stage] for hp in all_hops])
	stg_iter = lambda: xrange(max_stage+1)
	hops_from_stg = lambda s: filter(lambda q: q[stage] == s, all_hops)

	full_jumps = list()
	partial_jumps = None

	for stg in stg_iter():

		for hops in hops_from_stg(stg):
			if stg == 0:
				full_jumps.extend(hops)
				partial_jumps = hops
				continue
		if not partial_jumps:
			break
		for pj in partial_jumps:
			if hops[source] == pj[-1][dest]:
				new_jump = pj + (hops,)
				full_jumps.append(new_jump)
				partial_jumps.append(new_jump)
		longest = max([ len(pj) for pj in partial_jumps])
		partial_jumps = filter(lambda opj: len(opj) == longest, partial_jumps)

	for pj in partial_jumps:
		if not pj in full_jumps:
			full_jumps.append(pj)
	return full_jumps

def layout_pieces():
	# inclusive
	rc_map = dict(zip(range(BOARD_SIZE), [RED] * 3 + [EMPTY] * 2 + [BLACK] * 3))

	pieces = list()
	for row in xrange(BOARD_SIZE):
		row_color = rc_map[row]
		if row_color == EMPTY:
			continue
		s = (row+1) % 2
		pieces.extend([ rc_map[row], (2*n)+s, row ] for n in xrange(4))
	return [ Piece(c, x, y, False) for c, x, y in pieces ]

def print_game(grid, pieces):
	chr_map = { Disc:{RED:occupied_red, BLACK:occupied_black}, Cell:{RED:empty_red, BLACK:empty_black}}
	get_char = lambda c: chr_map[type(c)][c.color]
	grid_chars = [ [get_char(grid[x][y]) for x in xrange(BOARD_SIZE)] for y in xrange(BOARD_SIZE)]

	for p in pieces:
		pc = get_char(p)
		grid_chars[p.location.x][p.location.y] = pc

	trans_gc = [ [EMPTY] * BOARD_SIZE for q in xrange(BOARD_SIZE)]
	for x in xrange(BOARD_SIZE):
		for y in xrange(BOARD_SIZE):
			trans_gc[x][y] = grid_chars[y][x]

	print '\n'.join([ '\t'.join(trans_gc[r]) for r in xrange(BOARD_SIZE)])

def find_moves(color, pieces, occ_map):
	all_moves = list()
	for p in pieces:
		normal_moves = [ (p.x + mx, p.y + my) for mx, my in normal_movements]
		for nm_x, nm_y in normal_moves:
			if occ_map[nm_x][nm_y] == EMPTY:
				all_moves.append(Move(p, MOVE, ((nm_x, nm_y),), None, False))
			elif occ_map[nm_x][nm_y].color != p.color:
				jump_moves = try_jump(p, (nm_x, nm_y), (p.x, p.y), occ_map)
				if jump_moves:
					all_moves.extend(jump_moves)
	return all_moves

def play_turn(active_player, game_state):
	apc = colmap[active_player]
	p_map = defaultdict(lambda: defaultdict(lambda: EMPTY))
	for p in game_state:
		p_map[p.x][p.y] = p
	possible_moves = find_moves(apc, game_state, p_map)
	chosen_move = active_player.select(possible_moves)
	return apply_move(game_state)

def play_game(player1, player2):
	players = [player1, player2]
	colmap = dict(zip(COLORS, players))

	first_player = random.choice(players)
	turn_idx = 0

	initial_state = layout_pieces()
	history = list()

	game_state = initial_state
	while not game_over():
		active_player = players[(players.index(first_player) + turn_idx) % len(players)]
		new_state = play_turn(active_player, game_state)
		history.append({'turn_idx':turn_idx, 'active_player':active_player, 'state':new_state})
		game_state = new_state
		turn_idx += 1
	print history

def main():
	play_game('mike','katie')

if __name__ == '__main__':
	main()







