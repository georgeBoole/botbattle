


tile_types = (BRICK, ORE, WOOD, WHEAT, SHEEP, WATER, DESERT) = ('Brick', 'Ore', 'Lumber', 'Grain', 'Wool', 'Water', 'Desert')
resources = tile_types[:5]

resource_tile_coords = [
    (0,1), (0,2), (0,3),
    (1,0), (1,1), (1,2), (1,3),
    (2,-1), (2,0), (2,1), (2,2), (2,3),
    (3,-1), (3,0), (3,1), (3,2),
    (4,-1), (4,0), (4,1)
]

ADJACENCY_COORDINATE_MODIFIERS = [
    (0,-1), (1,-1), (1,0), (0,1), (-1,1), (-1,0)
]

acm = ADJACENCY_COORDINATE_MODIFIERS

PRODUCTION_NUMBERS = (2, 12) + reduce(lambda a,b: a + b, [ tuple([x] * 2) for x in [3,4,5,6,8,9,10,11] ])

TILE_QUANTITY = {
    BRICK:3,
    ORE:3,
    WOOD:4,
    WHEAT:4,
    SHEEP:4,
    DESERT:1
}