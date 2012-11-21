from bulbs.model import Node, Relationship, Edge
from bulbs.property import String, Integer, DateTime
from bulbs.utils import current_datetime

#config = Config(os.environ["NEO4J"])
#g = Graph(config)

class Tile(Node):
	element_type = 'tile'
	tile_type = String(nullable=False)
	production_number = Integer()
	x = Integer()
	y = Integer()

class Adjacency(Edge):
	label = 'touches'
	description = String(nullable=True)

class TileEdge(Edge):
	element_type = 'tileedge'

class TileVertex(Node):
	element_type = 'tilevertex'



