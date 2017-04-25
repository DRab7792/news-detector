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

def frange(x, y, jump):
	while x < y:
		yield x
		x += jump

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
		credible = 0
		if cur[4] == "Credible":
			credible = 1
		if sourceNode not in nodeMap:
			graph.add_node(sourceNode, {"longitude": 100, "type": "source", "credible": credible, "title": cur[3]})
			nodeMap.append(sourceNode)
		if eventNode not in nodeMap:
			graph.add_node(eventNode, {"longitude": 800, "type": "event", "credible": credible})
			nodeMap.append(eventNode)
		elif eventNode in nodeMap and credible == 1:
			graph.node[eventNode]["credible"] = 1

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
	evCentrality = nx.eigenvector_centrality(graph, 1000, 1e-2, None, 'weight')
	for nodeId, value in evCentrality.iteritems():
		graph.node[nodeId]["eigenvector"] = value
	return graph

def addCustomCentrality(graph, threshold): 
	for curNode in graph.nodes_iter():
		score = 0
		edges = graph.edges(curNode, data=True)
		for curEdge in edges:
			weight = curEdge[2]["weight"]
			if weight < threshold:
				score = score - abs(weight - threshold)
			elif weight > threshold or weight == threshold:
				score = score + (abs(weight - threshold) * 10)
		graph.node[curNode]["custom"] = score

	return graph

def addHitsCentrality(graph):
	hits = nx.hits(graph, 1000)
	# TODO - Adjust for tuple response
	for nodeId, value in hits[0].iteritems():
		graph.node[nodeId]["hub"] = value
	for nodeId, value in hits[1].iteritems():
		graph.node[nodeId]["authority"] = value
	return graph

def addDegreeCentrality(graph):
	degreeCentrality = nx.degree_centrality(graph)
	for nodeId, value in degreeCentrality.iteritems():
		graph.node[nodeId]["degreeCentrality"] = value
	return graph

def addDegree(graph):
	for cur in graph.nodes(data=True):
		cur[1]["degree"] = graph.degree(cur[0])
	return graph

def analyzeSourceResults(graph, attr, minThreshold, maxThreshold, step):
	results = {
		"threshold": [],
		"tp": [],
		"tn": [],
		"fp": [],
		"fn": [],
		"tpr": [],
		"fpr": [],
		"accuracy": [],
		"precision": []
	}
	for threshold in frange(minThreshold, maxThreshold, step):
		tp = 0.0
		tn = 0.0
		fp = 0.0
		fn = 0.0
		for cur in graph.nodes(data=True):
			curAttrs = cur[1]
			# if curAttrs["type"] != "source":
			# 	continue
			if curAttrs[attr] > threshold and curAttrs["credible"] == 1:
				tp = tp + 1.0
			elif curAttrs[attr] > threshold and curAttrs["credible"] == 0:
				fp = fp + 1.0
			elif curAttrs[attr] < threshold and curAttrs["credible"] == 0:
				tn = tn + 1.0
			else:
				fn = fn + 1.0

		accuracy = (tp + tn) / (tp + tn + fn + fp)
		precision = 0
		if (fp + tp) > 0:
			precision = tp / (fp + tp)
		tpr = tp / (fn + tp)
		fpr = fp / (tn + fp)

		results["threshold"].append(threshold)
		results["tp"].append(tp)
		results["tn"].append(tn)
		results["fp"].append(fp)
		results["fn"].append(fn)
		results["tpr"].append(tpr)
		results["fpr"].append(fpr)
		results["accuracy"].append(accuracy)
		results["precision"].append(precision)
		
	return results

def saveAnalysis(name, res):
	csv = "Threshold, True Positive Rate, False Positive Rate, Accuracy, Precision, True Positive, True Negative, False Positive, False Negative\n"

	# Append all the data
	for i in range(len(res["threshold"])):
		csv = csv + str(res["threshold"][i]) + ", "
		csv = csv + str(res["tpr"][i]) + ", "
		csv = csv + str(res["fpr"][i]) + ", "
		csv = csv + str(res["accuracy"][i]) + ", "
		csv = csv + str(res["precision"][i]) + ", "
		csv = csv + str(res["tp"][i]) + ", "
		csv = csv + str(res["tn"][i]) + ", "
		csv = csv + str(res["fp"][i]) + ", "
		csv = csv + str(res["fn"][i]) + "\n"

	file = open("data/analysis-" + name + ".csv", "w")
	file.write(csv)
	file.close()

def cleanString(val):
	if isinstance(val, unicode):
		val = val.encode('ascii', 'ignore')
	return str(val)

def exportGraphAsCSV(graph):
	header = "ID, "
	props = []
	body = ""

	first = True
	for cur in graph.nodes(data=True):
		curAttrs = cur[1]
		body = body + cur[0] + ", "
		if first:
			for attr, val in curAttrs.iteritems():
				header = header + str(attr).encode('ascii', 'ignore') + ", "
				props.append(attr)
				body = body + cleanString(val) + ", "

			first = False
			body = body + "\n"

		else:
			for prop in props:
				if prop not in curAttrs:
					body = body + ", "
				else:
					body = body + cleanString(curAttrs[prop]) + ", "
			body = body + "\n"

	csv = header + "\n" + body
	file = open("data/nodes.csv", "w")
	file.write(csv)
	file.close()


def degreeAnalysis(graph):
	print ("Add Degree Centralities")
	graph = addDegreeCentrality(graph)

	print ("Analyze degree centrality values")
	degreeRes = analyzeSourceResults(graph, "degreeCentrality", 0.0, 0.5, 0.01)

	print ("Save degree centrality values")
	saveAnalysis("degree", degreeRes)

def evAnalysis(graph):
	print ("Add EV Centralities")
	graph = addEigenVectorCentrality(graph)

	print ("Analyze ev centrality values")
	res = analyzeSourceResults(graph, "eigenvector", 0.0, 0.3, 0.005)

	print ("Save ev centrality values")
	saveAnalysis("ev", res)

def hitsAnalysis(graph):
	print ("Add Hits Centralities")
	graph = addHitsCentrality(graph)

	print ("Analyze ev centrality values")
	res = analyzeSourceResults(graph, "authority", 0.0, 0.1, 0.0005)

	print ("Save ev centrality values")
	saveAnalysis("authority", res)

	print ("Analyze ev centrality values")
	res = analyzeSourceResults(graph, "hub", 0.0, 0.1, 0.0005)

	print ("Save ev centrality values")
	saveAnalysis("hub", res)

def customAnalysis(graph, threshold):
	print ("Add Custom Centralities")
	graph = addCustomCentrality(graph, threshold)

	print ("Analyze custom values")
	customRes = analyzeSourceResults(graph, "custom", -20, 0, 1)

	print ("Save degree centrality values")
	saveAnalysis("custom-" + str(threshold), customRes)

def main():
	config = getConfig()

	db = mysql.connector.connect(user = config['db']['user'], password = config['db']['password'], host = config['db']['host'], database = config['db']['database'])

	print ("Get data")
	data = getData(db)

	print ("Form graph")
	graph = formGraph(data)

	addDegree(graph)

	evAnalysis(graph)

	degreeAnalysis(graph)

	customAnalysis(graph, 0)
	customAnalysis(graph, 5)
	customAnalysis(graph, 10)

	hitsAnalysis(graph)

	print ("Save graph")
	saveGraph(graph)

	exportGraphAsCSV(graph)


main()
