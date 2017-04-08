#!~/Library/Python/2.7
import requests  
import pip
import json
import arrow
import sys
import re
import string
import pandas as pd
import math
import numpy as np
from bs4 import BeautifulSoup  
from HTMLParser import HTMLParser
import mysql.connector
from slugify import slugify
from config import getConfig
from sklearn.metrics.pairwise import cosine_similarity
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 

FACTOR = 30

def parseArticles(articles):
	adjArticles = []
	for cur in articles:
		# print (cur[1])
		adjArticles.append({
			"id": cur[0],
			"words": json.loads(cur[1])
		})

	return adjArticles

def getArticles(db):
	# Ignore articles with empty word maps
	sql = "SELECT id, words  FROM articles WHERE words != '' AND CONCAT(title, description) != ''"
	cursor = db.cursor()
	cursor.execute(sql)
	return cursor.fetchall()

def calcWeight(a, b):
	weight = 0.0

	# Create sparse vectors
	allKeys = a.keys() + b.keys()

	# Get unique keys
	allKeys = list(set(allKeys))

	aVals = []
	bVals = []
	for key in allKeys:
		if key not in a:
			aVals.append(0.0)
		else:
			aVals.append(a[key])

		if key not in b:
			bVals.append(0.0)
		else:
			bVals.append(b[key])

	similarity = cosine_similarity(aVals, bVals)
	weight = similarity[0][0] * FACTOR

	return weight

def calcEdges(articles):
	edges = []
	# Iterate through all nodes
	for source in articles:
		print ("Source " + str(source["id"]))
		# Get the sorted source words
		sourceWords = sorted(source["words"], key=source["words"].get, reverse=True)

		for dest in articles:
			if source["id"] is dest["id"]:
				continue

			# Get the sorted dest words
			destWords = sorted(dest["words"], key=dest["words"].get, reverse=True)

			# Make sure the most frequent words appear in both lists
			if destWords[0] not in sourceWords or sourceWords[0] not in destWords:
				continue;

			weight = calcWeight(dest["words"], source["words"])

			# If weight is FACTOR, it is probably the same article
			if weight is FACTOR:
				print (str(source["id"]) + " is the same as " + str(dest["id"]))

			newEdge = {
				"source": source["id"],
				"dest": dest["id"],
				"weight": weight
			}

			edges.append(newEdge)


	return edges

def saveEdges(db, edges):

	perBatch = 500
	batches = int(math.ceil(len(edges)/perBatch))

	print ("Inserting " + str(len(edges)) + " into db, " + str(batches) + " batches")

	sql = "INSERT INTO articleLinks (source, dest, weight) VALUES (%s, %s, %s)"
	for batch in range(batches):
		print ("DB Batch " + str(batch))
		adjEdges = []
		for i in range((batch*perBatch), ((batch+1)*perBatch)):
			if i >= len(edges): 
				break
			cur = edges[i]
			adjEdges.append((
				str(cur["source"]),
				str(cur["dest"]),
				str(cur["weight"])
			))
		db.cursor().executemany(sql, adjEdges)
		db.commit()

	print ("Done")

def main():
	config = getConfig()

	db = mysql.connector.connect(user = config['db']['user'], password = config['db']['password'], host = config['db']['host'], database = config['db']['database'])

	articles = getArticles(db)

	articles = parseArticles(articles)

	edges = calcEdges(articles)

	saveEdges(db, edges)

main()