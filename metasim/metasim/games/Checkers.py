import random
from collections import namedtuple, defaultdict, Iterable

BOARD_SIZE = 8
DISCS_PER_PLAYER = 12
COLORS = (RED, BLACK) = ('Red', 'Black')
actions = (MOVE, JUMP) = ('move', 'jump')
EMPTY = 'Empty'

isodd = lambda n: n % 2 == 1
tile_color = lambda x,y: BLACK if isodd(x) == isodd(y) else RED
valid_loc = lambda r,t: r in legal_coords and t in legal_coords
dist = lambda a,b: abs(a[0]-b[0]) + abs(a[1]-b[1])

def midpoint(start_point, end_point):
	sx, sy, ex, ey = start_point + end_point
	return ((sx+ex)/2, (sy+ey)/2)

def get_neighbors(x, y, distance=1,remove_invalid=True):
	all_coords = [ (x+(dx*distance),y+(dy*distance)) for dx,dy in normal_movements]
	return filter(lambda r,s: valid_loc(r,s), all_coords) if remove_invalid else all_coords

def legally_directed_neighbors(c, x, y, d=1, all_le_d=False):
	if not all_le_d:
		return filter(lambda n_y: y > n_y if c is BLACK else y < n_y, get_neighbors(x,y,distance=d))
	else:
		return zip(*[ get_neighbors(x,y,distance=current_distance,remove_invalid=False) for current_distance in xrange(1, d+1) ])


normal_movements = [ (-1, -1), (-1, 1), (1, 1), (1, -1) ]
jump_movements = [ (-2,-2), (-2, 2), (2,2), (2,-2) ]
legal_coords = range(BOARD_SIZE)

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
Move = namedtuple('Move', ['piece', 'action', 'movement_path', 'was_made_king'])

class Checkers(object):

	def __init__(self, bots):
		self.players = bots
		self.initial_state = layout_pieces()
		self.final_state = None
		self.turn = 0
		self.game_over = False
		self.piece_count = dict(zip(COLORS, [12] * 2))
		self.color_map = dict(zip([BLACK, RED], self.players))
		self.loser = None
		self.winner = None

	def run(self):
		return self.play_game()

	def color_this_turn(self):
		return RED if isodd(self.turn_idx) else BLACK

	def play_game(self):
		self.turn_idx = 0
		initial_state = layout_pieces()

		game_record = list()
		game_state = initial_state
		game_record.append((game_state, None))
		last_size = len(game_state)
		while not self.game_over:
			game_state, move = self.play_turn(BLACK if self.turn_idx % 2 == 0 else RED, game_state)
			game_record.append((game_state, move))
			self.turn_idx += 1

		self.final_state = game_state
		if self.loser:
			self.winner = BLACK if self.loser == RED else RED
		return game_record

	@classmethod
	def find_piece_moves(cls, piece, occupancy_map):
		moves = list()
		#print str(legally_directed_neighbors(piece.color, piece.x, piece.y, d=2, all_le_d=True))
		for d1n, d2n in legally_directed_neighbors(piece.color, piece.x, piece.y, d=2, all_le_d=True):

			d1x, d1y = d1n if d1n else (None, None)
			d2x, d2y = d2n if d2n else (None, None)
			nbr = occupancy_map[d1x][d1y]
			if valid_loc(*d1n) and occupancy_map[d1n[0]][d1n[1]] == EMPTY:
				moves.append(Move(piece, MOVE, [(d1x,d1y)], d1y == 0 and piece.color == BLACK or d1y == BOARD_SIZE-1 and piece.color == RED))
			elif valid_loc(*d2n) and nbr.color != piece.color and occupancy_map[d2x][d2y] == EMPTY:
				occupancy_map_copy = occupancy_map.copy()
				fp = Piece(piece.color, d2x, d2y, piece.is_king or (d2y == 0 and piece.color == BLACK or d2y == BOARD_SIZE-1 and piece.color == RED))
				occupancy_map_copy[d2x][d2y] = fp
				occupancy_map_copy[d1x][d1y] = EMPTY
				occupancy_map_copy[piece.x][piece.y] = EMPTY
				nbr_jumps = filter(lambda x: x.action == JUMP, cls.find_piece_moves(fp, occupancy_map_copy))
				if nbr_jumps:
					moves.extend([ Move(piece, JUMP, [d2n] + nj.movement_path, fp.is_king or nj.was_made_king) for nj in nbr_jumps])
				else:
					moves.append(Move(piece, JUMP, [d2n], fp.is_king))
		return moves

	@classmethod
	def all_moves(cls, color, pieces, occ_map):
		return reduce(lambda x,y: x + y, map(lambda p: cls.find_piece_moves(p, occ_map), filter(lambda ap: ap.color == color, pieces)))

	def find_moves(self, move_color, pieces, occ_map):
		all_moves = Checkers.all_moves(move_color, pieces, occ_map)
		if not all_moves:
			return None
		has_jump = False
		for m in all_moves:
			if m.action == JUMP:
				has_jump = True
				break
		return all_moves if not has_jump else filter(lambda m: m.action == JUMP, all_moves)



	def apply_move(self, move, pieces):
		removed_locations = list()
		if move.action == JUMP:
			src = (move.piece.x, move.piece.y)
			for mp in move.movement_path:
				removed_locations.append(midpoint(src, mp))
				src = mp
		dstx, dsty = move.movement_path[-1]
		new_pieces = filter(lambda np: not (np.x, np.y) in removed_locations, map(lambda ap: Piece(ap.color, dstx, dsty, move.was_made_king) if ap == move.piece else ap, pieces))
		found_colors = list()
		for np in new_pieces:
			if not np.color in found_colors:
				found_colors.append(np.color)
				if len(found_colors) == 2:
					break
		if len(found_colors) < 2:
			self.loser = RED if BLACK == move.piece.color else BLACK
			self.game_over = True
		return new_pieces

	def play_turn(self, player_color, game_state):
		new_occupancy_map = defaultdict(lambda: defaultdict(lambda: EMPTY))
		for p in game_state:
			new_occupancy_map[p.x][p.y] = p

		possible_moves = self.find_moves(player_color, game_state, new_occupancy_map)
		if not possible_moves:
			self.game_over = True
			self.loser = player_color
			return game_state, None

		chosen_move = self.color_map[player_color].select(possible_moves)

		if chosen_move:
			return self.apply_move(chosen_move, game_state), chosen_move
		else:
			self.game_over = True
			self.loser = player_color
			return game_state, None


class CheckersBot(object):

	def __init__(self, name='robot'):
		self.name = name

	def select(self, possible_moves):
		return random.choice(possible_moves)

def main():
	bots = [ CheckersBot(n) for n in ('mike', 'karn')]
	fun_game = Checkers(bots)
	game_record = fun_game.run()
	#for item in game_record:
	#	print item
	print 'winner of the game was %s' % fun_game.winner
	print 'loser of the game was %s' % fun_game.loser




if __name__ == '__main__':
	main()







