import mysql.connector
import networkx as nx
from math import *
import inspect
import matplotlib.pyplot as plt
import numpy as np
# execfile("community.py")
from scipy.cluster.hierarchy import *
from operator import itemgetter
from config import getConfig

def getEdges(db, threshold):
	sql = "SELECT count(id) FROM articleLinks WHERE weight > " + str(threshold)
	cursor = db.cursor()
	cursor.execute(sql)
	numEdges = cursor.fetchone()
	numEdges = itemgetter(0)(numEdges)

	perBatch = 1000
	batches = int(ceil(numEdges/perBatch))
	batches = 5
	
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

def formClusteringLevels(links):
	levels = {}
	for i in range(0, 430, 10):
		nodeClusters = fcluster(links, float(i), 'distance')

		clusterDicts = {}

		for nodeId in range(len(nodeClusters)):
			clusterId = nodeClusters[nodeId]
			if clusterId in clusterDicts:
				clusterDicts[clusterId].append(nodeId)
			else:
				clusterDicts[clusterId] = [nodeId]

		levels[i] = clusterDicts

	return levels

# # Get all the nodes in a cluster
# def getClusterNodes(cluster):
# 	visited = set()
# 	queue = [cluster]
# 	nodes = []
# 	# Perform breadth first search
# 	while len(queue) > 0:
# 		curNode = queue.pop()
# 		if curNode and curNode not in visited:
# 			visited.add(curNode)

# 			# Create the levels map
# 			if curNode.is_leaf():
# 				# print ("curNode")
# 				# print (curNode.get_left())
# 				# print (curNode.get_right())
# 				nodes.append(curNode.get_id())
			
# 			left = curNode.get_left()
# 			right = curNode.get_right()
			
# 			queue.extend([left, right])
	
# 	return nodes

def subgraph(graph, nodes):
	newGraph = graph.copy()
	exclude = []
	for cur in newGraph.nodes_iter():
		if cur not in nodes:
			exclude.append(cur)
	newGraph.remove_nodes_from(exclude)
	return newGraph

def calcModularities(levels, graph):
	modularities = {}
	graphEdges = float(graph.number_of_edges())
	# Iterate through all levels
	for levelDist, clusters in levels.iteritems():
		levelModularities = []

		print ("-------------------------")
		print ("Level Distance: " + str(levelDist))

		# Iterate through clusters
		for clusterId, clusterNodes in clusters.iteritems():
			clusterGraph = graph.subgraph(clusterNodes).copy()
			clusterEdges = float(clusterGraph.number_of_edges())
			clusterDegree = 0

			for curNode in clusterGraph.nodes_iter():
				clusterDegree = clusterDegree + graph.degree(curNode)
			clusterDegree = float(clusterDegree)

			adj = (clusterEdges / graphEdges)
			rnd = pow((clusterDegree / (2 * graphEdges)), 2)


			print ("Cluster Nodes: " + str(len(clusterNodes)))
			# print (clusterNodes)
			print ("Cluster Graph Nodes: " + str(len(clusterGraph)))
			# print (clusterGraph.nodes())
			print ("Cluster Edges: " +  str(clusterEdges))
			print ("Real wiring: " +  str(adj))
			print ("Cluster degree: " +  str(clusterDegree))
			print ("Random: " + str(rnd))

			clusterModularity = adj - rnd

			levelModularities.append(clusterModularity)

		# Calculate modularity for whole level
		modularities[levelDist] = sum(levelModularities)

	return modularities


def saveEvents(clusters, graph, db):
	return


def graphModularities(modularities):
	# Sort modularities by dist
	xVals = sorted(modularities.keys())
	yVals = []
	maxI = 0
	maxVal = 0.0
	for i in xVals:
		if (modularities[i] > maxVal):
			maxVal = modularities[i]
			maxI = i
		yVals.append(modularities[i])

	plt.plot(xVals, yVals)
	plt.vlines(maxI, 0.0, (maxVal + 0.03), '#ff0000', 'dashed', "Optimal Modularity")
	plt.savefig("visualizations/modularities.png")
	plt.clf()

	return maxI

def cluster(graph):
	print ("Number of nodes: " + str(len(graph)))
	print ("Number of edges: " + str(graph.number_of_edges()))
	matrix = nx.to_numpy_matrix(graph)
	links = linkage(matrix, method='complete')
	order = leaves_list(links)
	
	
	tree = to_tree(links)
	levels = formClusteringLevels(links)
	# plotScreeplot(links)
	modularities = calcModularities(levels, graph)
	maxModularityDist = graphModularities(modularities)

	# Visualize
	dendrogram(
		links,
		truncate_mode='level',
		p=10,
		no_labels=True,
		show_leaf_counts=True
	)
	plt.hlines(maxModularityDist, 0, 2500, '#ff0000', 'dashed', "Optimal Modularity")
	plt.savefig("visualizations/articleLinksDendrogram.png")
	plt.clf()

def plotScreeplot(z):
	# Plotting
	plt.plot(range(1, len(z)+1), z[::-1, 2])
	knee = np.diff(z[::-1, 2], 2)
	plt.plot(range(2, len(z)), knee)

	num_clust1 = knee.argmax() + 2
	knee[knee.argmax()] = 0
	num_clust2 = knee.argmax() + 2

	plt.text(num_clust1, z[::-1, 2][num_clust1-1], 'possible\n<- knee point')

	part1 = fcluster(z, num_clust1, 'maxclust')
	part2 = fcluster(z, num_clust2, 'maxclust')

	clr = ['#2200CC' ,'#D9007E' ,'#FF6600' ,'#FFCC00' ,'#ACE600' ,'#0099CC' ,
	'#8900CC' ,'#FF0000' ,'#FF9900' ,'#FFFF00' ,'#00CC01' ,'#0055CC']

	# plt.setp(title='Screeplot', xlabel='partition', ylabel='cluster distance')
	plt.savefig('visualizations/screeplot.png')
	plt.clf()

def saveDendrogram(heirarchy):
	graph = nx.DiGraph(heirarchy)
	nodes = graph.nodes()
	leaves = set( n for n in nodes if graph.degree(n) == 0 )
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