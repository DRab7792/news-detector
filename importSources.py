import requests  
import json
import sys
from distutils.sysconfig import get_python_lib
import mysql.connector
from config import getConfig
from bs4 import BeautifulSoup  

def getSiteInfo(url, info):
	info['rss_feed'] = ""
	info['title'] = ""
	info['description'] = ""
	try:
		source_code = requests.get(url)
		plain_text = source_code.text
		soup = BeautifulSoup(plain_text, "lxml")
		info['title'] = soup.title.string
		rssLinks = soup.find_all("link", {"type" : "application/rss+xml"})
		if len(rssLinks) > 0:
			link = rssLinks[0]
			href = link.get('href')
			rssUrl = str(href)
			info['rss_feed'] = rssUrl
		descTags = soup.find_all("meta", {'name':'description'})
		if len(descTags) > 0:
			descTag = descTags[0]
			descText = descTag['content']
			info['description'] = descText
		return info
	except Exception as e:
		return info

def loadSources():
	sources = {}
	with open("sources/credible.json") as credibleJson:
		sources['credible'] = json.load(credibleJson)
	with open("sources/notCredible.json") as notCredibleJson:
		sources['notCredible'] = json.load(notCredibleJson)
	return sources

def assignFeeds(sources):
	completeSources = []
	# i = 0
	for type in iter(["notCredible"]):
		for url, info in sources[type].items():
			url = "http://" + url
			print ("Getting feed for " + url)
			if ('language' not in info):
				info['language'] = "en"
			info = getSiteInfo(url, info)
			info['credible'] = 0
			if (type == "credible"):
				info['credible'] = 1
				info['type'] = "Credible"
			info['url'] = url
			completeSources.append(info)
			# i = i + 1
			# if (i > 3):
			# 	break
			
	return completeSources
	
def saveSources(sources, db):
	# print (sources)
	adjSources = []
	sql = "INSERT INTO sources (title, url, rss_feed, type, language, credible, description) VALUES (%s, %s, %s, %s, %s, %s, %s)"
	# sql = "INSERT INTO sources (title, url, rss_feed, type, language, credible) VALUES (%s, %s, %s, %s, %s, %s)"
	for cur in sources:
		props = ["title", "url", "rss_feed", "type", "language", "description"]
		for prop in props:
			if (cur[prop] is None):
				cur[prop] = ""

		adjSources.append((
			cur['title'].encode('utf8'),
			cur['url'].encode('utf8'),
			cur['rss_feed'].encode('utf8'),
			cur['type'].encode('utf8'),
			cur['language'].encode('utf8'),
			str(cur['credible']),
			cur['description'].encode('utf8')
		))
	db.cursor().executemany(sql, adjSources)
	db.commit()

def main():
	config = getConfig()

	db = mysql.connector.connect(user = config['db']['user'], password = config['db']['password'], host = config['db']['host'], database = config['db']['database'])

	sources = loadSources()

	finishedSources = assignFeeds(sources)
	saveSources(finishedSources, db);
	
	db.close()

main()
# print (get_python_lib())