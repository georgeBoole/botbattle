
from py2neo import neo4j
import os

def wipe():
	graph_db = neo4j.GraphDatabaseService(os.environ['NEO4J_REST_URL'])
	graph_db.clear()

wipe()

