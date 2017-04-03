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

		# Form word dictionary
		text = cur[3] + " " + cur[5]
		text = text.lower()
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
	print (adjArticles[2])

main()