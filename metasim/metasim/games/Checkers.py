import random
from collections import namedtuple, defaultdict, Iterable
from itertools import permutations
import uuid

BOARD_SIZE = 8
DISCS_PER_PLAYER = 12
COLORS = (RED, BLACK) = ('Red', 'Black')
KING_LOC = {RED:BOARD_SIZE-1, BLACK:0}
SQUARE_STATES = (empty_red, empty_black, occupied_red, occupied_black) = ('=', '0', 'R', 'B')
actions = (MOVE, JUMP) = ('move', 'jump')
EMPTY = 'Empty'
jump_tuple_fields = (source, dest, victim, stage) = ('jump source', 'jump dest', 'jump victim', 'jump stage')

isodd = lambda n: n % 2 == 1
color = lambda x,y: BLACK if isodd(x) == isodd(y) else RED
valid_loc = lambda r,t: r in legal_coords and t in legal_coords
dist = lambda a,b: abs(a[0]-b[0]) + abs(a[1]-b[1])
def midpoint(start_point, end_point):
	sx, sy, ex, ey = start_point + end_point
	return [ v/2 for v in (sx+ex, sy+ey)]

def get_neighbors(x, y, distance=1,remove_invalid=True):
	all_coords = [ (x+(dx*distance),y+(dy*distance)) for dx,dy in normal_movements]
	return filter(lambda r,s: valid_loc(r,s), all_coords) if remove_invalid else all_coords

def can_jump(jumper_color, jumper_start, over, destination, omap):
	if not valid_loc(*destination) or omap[destination[0]][destination[1]] != EMPTY:
		return False
	return jumper_color != omap[over[0]][over[1]].color and dist(jumper_start,over) == 2 and dist(over,destination) == 2 and dist(jumper_start,destination) == 4

def build_jump(piece, hops):
	s_hops = sorted(hops, key=lambda h: h[3])
	mpath = set(reduce(lambda l,r: l + r, [ (hp[0], hp[1]) for hp in s_hops ]))
	p_rem = [ hp[2] for hp in s_hops ]
	return Move(piece, JUMP, mpath, p_rem, mpath[-1] == KING_LOC[piece.color])

def valid_nonjump_move(piece, start_location, end_location):



def _try_jump(piece, target, occupancy_map, stage):
	src = piece.x, piece.y
	dst = target
	btwn = midpoint(src, dst)
	stg = stage
	hops = list()
	while can_jump(piece.color, src, btwn, dst, occupancy_map):
		hops.append((src, dst, occupancy_map[btwn[0]][btwn[1]], stg))
		stg += 1
		src = dst



def try_jump(piece, target, jumper, occupancy_map):
	all_hops = _try_jump(piece, target, occupancy_map, 0)
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


normal_movements = [ (-1, -1), (-1, 1), (1, 1), (1, -1) ]
jump_movements = [ (-2,-2), (-2, 2), (2,2), (2,-2) ]
legal_coords = range(BOARD_SIZE)



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


Piece = namedtuple('Piece', ['color', 'x', 'y', 'is_king'])
Move = namedtuple('Move', ['piece', 'action', 'movement_path', 'pieces_removed', 'was_made_king'])
TURN_LIMIT = 5

class Checkers(object):

	def __init__(self, bots):
		self.players = bots
		self.initial_state = layout_pieces()
		self.final_state = None
		self.turn = 0
		self.game_over = False
		self.piece_count = dict(zip(COLORS, [12] * 2))

	def run(self):
		self.play_game()

	def color_this_turn(self):
		return RED if isodd(self.turn_idx) else BLACK

	def play_game(self):
		self.turn_idx = 0
		initial_state = layout_pieces()

		game_state = initial_state
		active_player = None
		self.first_player = self.players[0]
		while not self.game_over:
			active_player = self.first_player if active_player != self.first_player else filter(lambda b: b != self.first_player, self.players).pop()
			game_state = self.play_turn(active_player, game_state)

			self.turn_idx += 1
		self.final_state = game_state

	@rules_enforced
	def find_moves(self, color, pieces, occ_map):
		all_moves = list()
		for p in pieces:
			for nm_x, nm_y in get_neighbors(p.x, p.y):
				if occ_map[nm_x][nm_y] == EMPTY:
					all_moves.append(Move(p, MOVE, ((nm_x, nm_y),), None, False))
				elif occ_map[nm_x][nm_y].color != p.color:
					jump_moves = try_jump(p, (nm_x, nm_y), (p.x, p.y), occ_map)
					if jump_moves:
						all_moves.extend(jump_moves)
		if not all_moves:
			self.game_over = True
		return all_moves

	def apply_move(self, move, pieces):
		dead_pieces = []
		if move.pieces_removed:
			dead_pieces = filter(lambda ded_pc: ded_pc, move.pieces_removed)
			if dead_pieces:
				for dp in dead_pieces:
					self.piece_count[dp.color] =- 1
		m = move
		dx, dy = m.movement_path[-1] if isinstance(m.movement_path, Iterable) else m.movement_path
		replacement_piece = Piece(m.piece.color, dx, dy, m.was_made_king)
		return filter(lambda p: not p in dead_pieces, map(lambda q: replacement_piece if m.piece == q else q, pieces ))

	def play_turn(self, active_player, game_state):
		print 'Beginning turn %d, %s turn' % (self.turn_idx, active_player.name)
		p_map = defaultdict(lambda: defaultdict(lambda: EMPTY))
		for p in game_state:
			p_map[p.x][p.y] = p

		#print 'active player is %s and is found in the color dict? %s' % (active_player.name, active_player in self.player_color)
		possible_moves = self.find_moves(self.color_this_turn, game_state, p_map)
		chosen_move = active_player.select(possible_moves)
		return self.apply_move(chosen_move, game_state)


class CheckersBot(object):

	def __init__(self, name='robot'):
		self.name = name

	def select(self, possible_moves):
		return random.choice(possible_moves)

def main():
	#play_game('mike','katie')
	bots = [ CheckersBot(n) for n in ('mike', 'karn')]
	fun_game = Checkers(bots)
	fun_game.run()




if __name__ == '__main__':
	main()







