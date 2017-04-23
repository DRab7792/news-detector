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

def getData(db):
	sql = "SELECT count(a.id) as `weight`, a.event as `event_id`, a.source as `source_id`, b.title as `source_title`, b.type as `type` FROM `articles` a INNER JOIN sources b ON a.source = b.id AND a.event > 0 AND a.source > 0 GROUP BY a.event, a.source ORDER BY weight DESC"
	cursor = db.cursor()
	cursor.execute(sql)
	data = cursor.fetchall()
	return data

def formGraph(data):
	graph = nx.Graph()
	
	nodeMap = []
	sourceLat = 0
	eventLat = 0
	for cur in data:
		# Add nodes
		sourceNode = "source-" + str(cur[2])
		eventNode = "event-" + str(cur[1])
		if sourceNode not in nodeMap:
			credible = 0
			if cur[4] is "Credible":
				credible = 1
			graph.add_node(sourceNode, {"longitude": 100, "type": "source", "credible": credible, "title": cur[3]})
			nodeMap.append(sourceNode)
		if eventNode not in nodeMap:
			graph.add_node(eventNode, {"longitude": 800, "type": "event"})
			nodeMap.append(eventNode)

		# Add edges
		graph.add_edge(sourceNode, eventNode, {"weight": cur[0]})

	# Form geo layout
	for curNode in graph.nodes(data=True):
		if curNode[1]['type'] == "event":
			curNode[1]['latitude'] = eventLat
			eventLat = eventLat + 100
			# print "Event lat: " + str(eventLat)
			# print (graph.degree(curNode[0]))
		elif curNode[1]['type'] == "source":
			curNode[1]['latitude'] = sourceLat
			sourceLat = sourceLat + 100
			# print "Source lat: " + str(sourceLat)
			# print (graph.degree(curNode[0]))

	return graph.to_undirected()

def saveGraph(graph):
	nx.write_gml(graph, "data/sourceEvents.gml")

def addEigenVectorCentrality(graph):
	evCentrality = nx.eigenvector_centrality(graph, 100, 1e-06, None, 'weight')
	for nodeId, value in evCentrality.iteritems():
		graph.node[nodeId]["eigenvector"] = value
	return graph

def 

def analyzeSourceResults(graph, attr, threshold):
	tp = 0
	tn = 0
	fp = 0
	fn = 0
	for cur in graph.nodes(data=True):
		curAttrs = cur[1]
		if curAttrs[attr] > threshold and curAttrs["credible"] == 1:
			tp = tp + 1
		elif curAttrs[attr] > threshold and curAttrs["credible"] == 0:
			fp = fp + 1
		elif curAttrs[attr] < threshold and curAttrs["credible"] == 0:
			tn = tn + 1
		else:
			fn = fn + 1

	accuracy = (tp + tn) / (tp + tn + fn + fp)
	precision = tp / (fp + tp)
	tpr = tp / (fn + tp)
	fpr = fp / (tn + fp)

	print ("-------------")
	print ("Results")
	print ("-------------")
	print ("Accuracy: " + str(accuracy))
	print ("Precision: " + str(precision))
	print ("True Positive Rate: " + str(tpr))
	print ("False Positive Rate: " + str(fpr))


def main():
	config = getConfig()

	db = mysql.connector.connect(user = config['db']['user'], password = config['db']['password'], host = config['db']['host'], database = config['db']['database'])

	print ("Get data")
	data = getData(db)

	print ("Form graph")
	graph = formGraph(data)

	print ("Save graph")
	saveGraph(graph)

	print ("Add Eigenvector Centralities")
	graph = addEigenVectorCentrality(graph)

	print ("Analyze eigenvector values")
	analyzeSourceResults(graph, "eigenvector", 0.5)


main()
