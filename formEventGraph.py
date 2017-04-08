import mysql.connector
import networkx as nx
import math
from operator import itemgetter
from config import getConfig

def getEdges(db):
	sql = "SELECT count(id) FROM articleLinks"
	cursor = db.cursor()
	cursor.execute(sql)
	numEdges = cursor.fetchone()
	numEdges = itemgetter(0)(numEdges)

	perBatch = 500
	batches = int(math.ceil(numEdges/perBatch))
	# batches = 1
	
	edges = []
	for batch in range(batches):
		print ("Getting batch " + str(batch))
		sql = "SELECT * FROM articleLinks LIMIT " + str(perBatch)
		sql += " OFFSET " + str(batch * perBatch)
		cursor = db.cursor()
		cursor.execute(sql)
		batchEdges = cursor.fetchall()
		edges = edges + batchEdges

	return edges

def parseEdges(edges):
	adjEdges = []
	for cur in edges:
		adjEdges.append({
			"id": int(cur[0]),
			"source": int(cur[1]),
			"dest": int(cur[2]),
			"weight": float(cur[3])
		})
	return adjEdges

def getArticles(db):
	# Ignore articles with empty word maps
	sql = "SELECT a.id as `id`, a.title as `article_title`, b.title as `source_title` FROM `articles` a  INNER JOIN `sources` b ON a.source = b.id"
	cursor = db.cursor()
	cursor.execute(sql)
	return cursor.fetchall()

def parseArticles(articles):
	adjArticles = []
	for cur in articles:
		adjArticles.append({
			"id": cur[0],
			"title": cur[1],
			"source": cur[2]
		})
	return adjArticles

def formGraph(nodes, edges):
	graph = nx.Graph()

	for cur in nodes:
		graph.add_node(cur["id"], cur)

	for cur in edges:
		graph.add_edge(cur["source"], cur["dest"], cur)

	return graph.to_undirected()

def saveGraph(graph):
	nx.write_gml(graph, "data/article-similarities.gml")

def main():
	config = getConfig()

	db = mysql.connector.connect(user = config['db']['user'], password = config['db']['password'], host = config['db']['host'], database = config['db']['database'])

	print ("Get edges")
	edges = getEdges(db)

	print ("Parse edges")
	edges = parseEdges(edges)

	print ("Get articles")
	articles = getArticles(db)

	print ("Parse articles")
	articles = parseArticles(articles)

	print ("Form Graph")
	graph = formGraph(articles, edges)

	print ("Save graph")
	saveGraph(graph)

main()