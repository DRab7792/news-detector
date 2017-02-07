#!~/Library/Python/2.7
import requests  
import pip
import json
import sys
import lxml
from bs4 import BeautifulSoup  
import mysql.connector
from slugify import slugify
from config import getConfig
from google.cloud import language
from nltk.stem.porter import PorterStemmer

def getAndParseFeed(source, url, existingIds):
	articles = []

	# Try to get the feed
	try:
		source_code = requests.get(url)
		plain_text = source_code.text
		soup = BeautifulSoup(plain_text, "lxml")
		items = soup.findAll("item")

		# Find all items in the feed
		for cur in items:

			# Parse item
			article = {
				"source": source
			}
			props = ["title", "link", "description", "guid", "pubdate"]
			for prop in props:
				if getattr(cur, prop) is not None:
					val = getattr(cur, prop).text
					article[prop] = val

			# Exclude existing articles
			if article["guid"] in existingIds:
				continue

			# Get any category tags
			catTags = cur.findAll("category")
			categories = ""
			for cat in catTags:
				categories = categories + cat.text + ". "
			article["categories"] = categories

			# Add to articles list
			articles.append(article)

		return articles
			
	except Exception as e:
		print ("Error parsing feed: " + str(e))
		return articles


def analyzeArticles(articles, langClient):
	for cur in articles:
		text = cur['title'] + " " + cur['description'] + " " + cur['categories']
		# print (text)
		document = langClient.document_from_text(text)
		entities = document.analyze_entities()
		cur['analysis'] = {
			"where": {},
			"who": {},
			"what": {},
			"when": ""
		}
		if "pubdate" in cur:
			cur['analysis']['when'] = cur['pubdate']
		for curEntity in entities:
			curType = "what"
			name = curEntity.name
			if curEntity.entity_type == "PERSON":
				curType = "who"
			elif curEntity.entity_type == "LOCATION" or curEntity.entity_type == "EVENT":
				curType = "where"
			slug = slugify(name)
			if slug not in cur["analysis"][curType]:
				cur["analysis"][curType][slug] = 1
			else:
				cur["analysis"][curType][slug] = cur["analysis"][curType][slug] + 1
		# print (cur["analysis"])

			
	return articles


def getSourcesWithFeeds(db):
	sql = "SELECT id, title, rss_feed FROM sources WHERE rss_feed != ''"
	cursor = db.cursor()
	cursor.execute(sql)
	return cursor.fetchall()

def getExistingArticleIds(db, id):
	sql = "SELECT source_id FROM articles WHERE source = '" + str(id) + "'"
	cursor = db.cursor()
	cursor.execute(sql)
	return cursor.fetchall()

def saveArticles(db, articles):
	adjArticles = []
	sql = "INSERT INTO articles (source, title, url, description, source_id, time, who, what, loc) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
	for cur in articles:
		adjArticles.append((
			str(cur["source"]),
			cur["title"].encode("utf8"),
			cur["link"].encode("utf8"),
			cur["description"].encode("utf8"),
			cur["guid"].encode("utf8"),
			cur["analysis"]["when"].encode("utf8"),
			json.dumps(cur["analysis"]["who"]),
			json.dumps(cur["analysis"]["what"]),
			json.dumps(cur["analysis"]["where"])
		))
	db.cursor().executemany(sql, adjArticles)
	db.commit()

def main():
	config = getConfig()
	langClient = language.Client()

	db = mysql.connector.connect(user = config['db']['user'], password = config['db']['password'], host = config['db']['host'], database = config['db']['database'])

	sourceFeeds = getSourcesWithFeeds(db)
	
	for (id, title, rss_feed) in sourceFeeds:
		existingIds = getExistingArticleIds(db, id)
		articles = getAndParseFeed(id, rss_feed, existingIds)
		analyzeArticles(articles, langClient)
		saveArticles(db, articles)
		# break

main()
# import pip
# installed_packages = pip.get_installed_distributions()
# installed_packages_list = sorted(["%s==%s" % (i.key, i.version)
#      for i in installed_packages])
# print(installed_packages_list)