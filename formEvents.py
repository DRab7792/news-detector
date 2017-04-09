import mysql.connector
import networkx as nx
import math
import inspect
import matplotlib.pyplot as plt
execfile("community.py")
from scipy.cluster.hierarchy import dendrogram
from operator import itemgetter
from config import getConfig

def getEdges(db, threshold):
	sql = "SELECT count(id) FROM articleLinks WHERE weight > " + str(threshold)
	cursor = db.cursor()
	cursor.execute(sql)
	numEdges = cursor.fetchone()
	numEdges = itemgetter(0)(numEdges)

	perBatch = 1000
	batches = int(math.ceil(numEdges/perBatch))
	# batches = 50
	
	edges = []
	for batch in range(batches):
		print ("Getting batch " + str(batch))
		sql = "SELECT * FROM articleLinks WHERE weight > " + str(threshold) + " LIMIT " + str(perBatch)
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
			"title": cur[1].encode('ascii', 'ignore'),
			"source": cur[2].encode('ascii', 'ignore')
		})
	return adjArticles

def formGraph(nodes, edges):
	graph = nx.Graph()

	for cur in nodes:
		graph.add_node(cur["id"], cur)

	for cur in edges:
		graph.add_edge(cur["source"], cur["dest"], cur)

	return graph.to_undirected()

def removeOrphans(graph):
	solitary=[ n for n,d in graph.degree_iter() if d==0 ]
	for cur in solitary:
		graph.remove_node(cur)
	return graph

def saveGraph(graph, threshold):
	nx.write_gml(graph, "data/article-similarities" + str(threshold) + ".gml")

def cluster(graph):
	dendrogram = generate_dendrogram(graph)
	print (len(dendrogram))
	for level in range(len(dendrogram)):
		curPartition = partition_at_level(dendrogram, level)
		print ("length of partition at level", level, "is", len(curPartition.keys()))
	return dendrogram

def saveDendrogram(heirarchy):
	graph = nx.DiGraph(heirarchy)
	nodes = graph.nodes()
	leaves      = set( n for n in nodes if graph.degree(n) == 0 )
	inner_nodes = [ n for n in nodes if graph.degree(n) > 0 ]

	# Compute the size of each subtree
	subtree = dict( (n, [n]) for n in leaves )
	for u in inner_nodes:
	    children = set()
	    node_list = list(d[u])
	    while len(node_list) > 0:
	        v = node_list.pop(0)
	        children.add( v )
	        node_list += d[v]

	    subtree[u] = sorted(children & leaves)

	inner_nodes.sort(key=lambda n: len(subtree[n]))

	# Construct the linkage matrix
	leaves = sorted(leaves)
	index  = dict( (tuple([n]), i) for i, n in enumerate(leaves) )
	Z = []
	k = len(leaves)
	for i, n in enumerate(inner_nodes):
	    children = d[n]
	    x = children[0]
	    for y in children[1:]:
	        z = tuple(subtree[x] + subtree[y])
	        i, j = index[tuple(subtree[x])], index[tuple(subtree[y])]
	        Z.append([i, j, float(len(subtree[n])), len(z)]) # <-- float is required by the dendrogram function
	        index[z] = k
	        subtree[z] = list(z)
	        x = z
	        k += 1

	# Visualize
	dendrogram(Z, labels=leaves)
	plt.savefig("visualizations/articleLinksDendrogram.png");

def main():
	threshold = 20

	config = getConfig()

	db = mysql.connector.connect(user = config['db']['user'], password = config['db']['password'], host = config['db']['host'], database = config['db']['database'])

	print ("Get edges")
	edges = getEdges(db, threshold)

	print ("Parse edges")
	edges = parseEdges(edges)

	print ("Get articles")
	articles = getArticles(db)

	print ("Parse articles")
	articles = parseArticles(articles)

	print ("Form Graph")
	graph = formGraph(articles, edges)

	print ("Eliminate Orphans")
	graph = removeOrphans(graph)

	print ("Perform Heriarchical Clustering")
	dendrogram = cluster(graph)

	# print ("Save dendrogram with modularity")
	# dendrogram = saveDendrogram(dendrogram, modularity)

	print ("Save graph")
	saveGraph(graph, threshold)

main()