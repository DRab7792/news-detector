import mysql.connector
import networkx as nx
from math import *
import inspect
import json
import matplotlib.pyplot as plt
import numpy as np
from scipy.cluster.hierarchy import *
from operator import itemgetter
from config import getConfig

def getData(db):
	sql = "SELECT event, words FROM articles WHERE event > 0"
	cursor = db.cursor()
	cursor.execute(sql)
	data = cursor.fetchall()
	return data

def formEventData(data):
	eventMap = {}

	# Form the event map
	for cur in data:
		index = cur[0]
		keywords = json.loads(cur[1].encode('ascii', 'ignore'))
		# Handle the number of articles
		if index not in eventMap.keys():
			eventMap[index] = {
				"numArticles": 1,
				"keywords": {}
			}
		else:
			eventMap[index]["numArticles"] = eventMap[index]["numArticles"] + 1
		
		# Handle the keyword dict
		for term, score in keywords.iteritems():
			term = term.encode('ascii', 'ignore')
			if type(eventMap[index]["keywords"]) is dict and term is not '':
				if term in eventMap[index]["keywords"].keys():
					eventMap[index]["keywords"][term] = eventMap[index]["keywords"][term] + score
				else:
					eventMap[index]["keywords"][term] = score


	# Sort the keywords
	for curId, cur in eventMap.iteritems():
		print ("-----------")
		keywords = sorted(cur["keywords"], key=cur["keywords"].get, reverse=True)
		i = 0
		adjKeywords = {}
		for term in keywords:
			print (term + ": " + str(cur["keywords"][term]))

			if i >= 8:
				break

			adjKeywords[term] = cur["keywords"][term]
			
			i = i + 1
		cur["keywords"] = adjKeywords

	# print (eventMap)
	return eventMap

def saveEventData(data, db):
	sql = "INSERT INTO events (id, num_articles, keywords) VALUES (%s, %s, %s)"
	vals = []
	for curId, cur in data.iteritems():
		vals.append((
			str(curId), 
			str(cur["numArticles"]),
			json.dumps(cur["keywords"])
		))
	db.cursor().executemany(sql, vals)
	db.commit()


def main():
	config = getConfig()

	db = mysql.connector.connect(user = config['db']['user'], password = config['db']['password'], host = config['db']['host'], database = config['db']['database'])

	print ("Get events")
	articleData = getData(db)

	print ("Form event data")
	eventData = formEventData(articleData)

	print ("Saving event data")
	saveEventData(eventData, db)

main()