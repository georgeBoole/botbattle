from py2neo import neo4j, cypher
import os

rest_url = os.environ.get('NEO4J_REST_URL')
graphdb_server_url = rest_url if rest_url else 'http://localhost:7474'
graph_db = neo4j.GraphDatabaseServer(graphdb_server_url)

