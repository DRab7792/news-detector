#!~/Library/Python/2.7
import requests  
import pip
import json
import arrow
import sys
import re
import string
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup  
from HTMLParser import HTMLParser
import mysql.connector
from slugify import slugify
from config import getConfig
import nltk
from nltk.corpus import stopwords
from nltk.stem.lancaster import LancasterStemmer
nltk.download("stopwords")
st = LancasterStemmer()

timeFormat = "ddd, DD MMM YYYY HH:mm:ss ZZ"
timeFormatAlt = "ddd, D MMM YYYY HH:mm:ss ZZ"

ENTITY_WEIGHT = 1.5

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def parseArticles(articles):
	global timeFormat
	adjArticles = []
	for cur in articles:
		if (len(cur) != 12):
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

		# Form word dictionary
		text = cur[3] + " " + cur[5]
		text = text.lower()
		s = MLStripper()
		s.feed(text)
		text = s.get_data()
		words = string.split(text, " ")
		words = [word for word in words if word not in stopwords.words('english')]
		numWords = len(words)
		wordDict = {}
		for curWord in words:
			curWord = re.sub(r'[^\w\s]','',curWord)
			curWord = st.stem(curWord)
			if curWord in wordDict:
				wordDict[curWord] = wordDict[curWord] + 1
			else:
				wordDict[curWord] = 1

		# Normalize word frequency
		for curWord, freq in wordDict.items():
			wordDict[curWord] = float(freq) / numWords

		# Append article data to new array
		adjArticle = {
			"id": cur[0],
			"time": time,
			"who": who,
			"what": what,
			"loc": loc,
			"title": cur[3],
			"description": cur[5],
			"words": wordDict
		}
		
		adjArticles.append(adjArticle)

	return adjArticles

# Increase the weight of terms that Google said are entities
def weighEntities(articles):
	adjArticles = []
	# Iterate through all articles
	for cur in articles:
		keys = cur["words"].keys()

		# Iterate through the entitiy properties and form one long entity string for easy detection
		entityProps = ["who", "what", "loc"]
		entityString = ""
		for prop in entityProps:

			# If the property is not defined, move onto the next one
			if prop not in cur:
				continue

			entityString = entityString + "-".join(cur[prop].keys())

		for word in cur["words"]:
			if word in entityString:
				cur["words"][word] = cur["words"][word] * ENTITY_WEIGHT

		adjArticles.append(cur)

	return adjArticles

def trimWordMaps(articles):
	adjArticles = []
	# Iterate through all articles
	for cur in articles:

		# Sort the words by value
		sortedWords = sorted(cur["words"], key=cur["words"].get, reverse=True)

		# Take the top 8 words
		adjWords = {}
		i = 0

		for curWord in sortedWords:
			if i >= 8:
				break

			adjWords[curWord] = cur["words"][curWord]

			i = i + 1

		cur["words"] = adjWords

		adjArticles.append(cur)

	return adjArticles

def saveArticles(db, articles):
	sql = "UPDATE articles SET words = %s WHERE id = %s"
	vals = []
	for cur in articles:
		vals.append((
			json.dumps(cur["words"]),
			str(cur["id"])
		))
	db.cursor().executemany(sql, vals)
	db.commit()

def getArticles(db):
	# Only get new articles
	sql = "SELECT * FROM articles WHERE words = ''"
	cursor = db.cursor()
	cursor.execute(sql)
	return cursor.fetchall()

def main():
	config = getConfig()

	db = mysql.connector.connect(user = config['db']['user'], password = config['db']['password'], host = config['db']['host'], database = config['db']['database'])

	articles = getArticles(db)

	articles = parseArticles(articles)

	articles = weighEntities(articles)

	articles = trimWordMaps(articles)

	saveArticles(db, articles)

main()