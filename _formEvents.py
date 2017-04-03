#!~/Library/Python/2.7
import requests  
import pip
import json
import arrow
import sys
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup  
import mysql.connector
from slugify import slugify
from config import getConfig
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans

timeFormat = "ddd, DD MMM YYYY HH:mm:ss ZZ"
timeFormatAlt = "ddd, D MMM YYYY HH:mm:ss ZZ"

def parseArticles(articles):
	global timeFormat
	adjArticles = []
	for cur in articles:
		if (len(cur) != 11):
			continue

		# Try to parse time
		time = cur[7]
		if time == "": 
			continue
		time = time.replace("GMT", "+00:00")
		time = time.replace("PST", "-08:00")
		time = time.replace("EDT", "-05:00")
		try:
			time = arrow.get(time, timeFormat)
		except Exception as e:
			time = arrow.get(time, timeFormatAlt)
			continue
		
		# Parse the json objects
		who = json.loads(cur[8])
		what = json.loads(cur[9])
		loc = json.loads(cur[10])

		# Append article data to new array
		adjArticle = {
			"id": cur[0],
			"time": time,
			"who": who,
			"what": what,
			"loc": loc,
			"title": cur[3]
		}
		
		adjArticles.append(adjArticle)

	return adjArticles

def formIdf(articles):
	matrix = {}

	# Create document id map
	docMap = {}
	ids = []
	titles = []
	emptyArr = []
	i = 0
	for cur in articles:
		docMap[cur["id"]] = i
		ids.append(cur["id"])
		titles.append(cur["title"])
		emptyArr.append(0)
		i = i + 1

	maxVal = 0
	maxWord = ""
	for curArticle in articles:
		maps = ["who", "what", "loc"]
		for curMap in maps:
			for word, num in curArticle[curMap].items():
				if num > maxVal:
					maxVal = num
					maxWord = word
				if word not in matrix:
					matrix[word] = list(emptyArr)
				matrix[word][docMap[curArticle["id"]]] = num

	print ("Words in matrix: " + str(len(matrix)))
	print ("Maximum occurances of word in a single doc: " + str(maxVal))
	print ("Most popular word: " + word)

	# Form actual matrix
	lists = []
	for word, arr in matrix.items():
		lists.append(arr)

	return lists, ids, titles


def getArticles(db):
	sql = "SELECT * FROM articles WHERE event = 0 LIMIT 200"
	cursor = db.cursor()
	cursor.execute(sql)
	return cursor.fetchall()

def main():
	config = getConfig()

	db = mysql.connector.connect(user = config['db']['user'], password = config['db']['password'], host = config['db']['host'], database = config['db']['database'])

	articles = getArticles(db)

	adjArticles = parseArticles(articles)

	words, ids, titles = formIdf(adjArticles)

	dist = 1 - cosine_similarity(words)
	
	num_clusters = 20
	km = KMeans(n_clusters=num_clusters)

	km.fit(words)

	clusters = km.labels_.tolist()

	articleData = { 'title': titles, 'cluster': clusters, 'id': ids}

	frame = pd.DataFrame(articleData, index = [clusters], columns = ['title', 'cluster', 'id'])

	print (frame['cluster'].value_counts())

main()