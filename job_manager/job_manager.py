

######################################################################################################
## Times of india scraping
##
##
######################################################################################################


from lxml import html
import requests
from newspaper import Article
from bs4 import BeautifulSoup
import datetime
import dateutil.parser
import threading
from db_connect import Database
from google_images_download import google_images_download
from variables import *

# databse oblject
db = Database()
# retuens all the articles from added and failed
bd_article_list = db.get_all_article_url()

def _get_links(source):
	"""
	Finds all possible links present on perticular page
	returns list of all href
	"""
	# reques to main source and get the content
	try:
		page = requests.get(source, timeout=60, verify=True)
		webpage = html.fromstring(page.content)
		# finds the list of all link presnt on main source page
		links = webpage.xpath('//a/@href')
		return(links)
	except Exception as e:
		print("failed to get list of articles from %s" %(source))
		# return empty list if it fails
		return []

def _get_image(title):
	"""
	Searches for the single image
	Input: keywords
	Output: returns single image path
	"""
	arguments = {"keywords": title,
				"limit":1,
				"format": "jpg",
				"no_download":True}

	path = response.download(arguments)

	# path is tuple so path[0]
	# path[0][title] is dict for key as title and list_of image as value
	# path[0][title][0] to pick first image from list
	return (path[0][title][0])

def _filter_and_push_article(source, category):
	"""
	filters out the artical according to date
	pushes the data in db if artical is not old
	data pushed:
		1. title
		2. date
		3. keywords
		4. text
		5. image link
		6. catogary
		7. source link
	"""
	#print(source)
	global article_added
	article_date = ""
	# creates object of artial
	# memoize_articles is set to true to save in cache for avoiding latency
	article = Article(url=source, memoize_articles = True, request_timeout=30)

	# Download will download all the page content
	article.download()
	# Parse will parse the html content
	article.parse()
	# nlp will do get all the requied data link title, text, keywords etc
	article.nlp()

	# query to insert the artile news
	query_string = "INSERT INTO News (url,title,created_date,text,keywords,category,location,image) "

	# remove the unneccessary quotes
	title = article.title.replace('"',"'").replace("“","'").replace("”","'")
	# genetate the created data in required Mysql format
	created_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	# remove the unneccessary quotes and next line
	text = article.text.replace('\n',' ').replace('"',"'").replace("“","'").replace("”","'")
	# if the summay is more than 500 words truncate the text to 500 words
	if len(text) > 5000:
		text = text[:4999]

	# if text and title are empty then the article failed to get the requred data
	# add this article in failed table for later use
	# also return if this case happens
	if text is "" or title is "" :
		query_string_issue = "INSERT INTO failed_news (url,created_date,error) "
		values = 'values("%s","%s","%s")' %(source, created_date, 
			"NO text and Tile found")
		db.query(query_string + values)
		return

	# importent keywords from the article
	keywords = ",".join(article.keywords)
	# location is India
	# TODO
	# - This need to be changed to acurate location with city wise
	location = 'India'
	# Top search image on the article page
	image = article.top_image

	# get new image if the article is having default image
	if image is toi_image_default:
		image = _get_image(title)
	# Add values and generate the string for query
	values = 'values("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")' %(source,title,created_date,text,keywords,category,location,image)

	print(query_string + values)

	# push into db
	db.query(query_string + values)
	# after pushing inc the counter for added article
	article_added = article_added+1
	print(article_added)

def _filter_out_category(categories_raw):
	# intilize a null list
	unique_list = []

	# traverse for all elements
	for category in categories_raw:
		# check if exists in unique_list or not
		if category not in unique_list and len(category) > 1:
			unique_list.append(category)
	return unique_list

def _scan_and_push_category(category):
	#print(category)
	source = source_page + category
	cms_links = _get_links(source)
	for link in cms_links:
		# filter .cms link
		# last 4 char should be alwas .cms
		if '.cms' in link[-4:]:
			url = link
			# add source page url if not present
			if link[0] is '/':
				url = source_page + link
			if 'http' not in link:
				url = source_page + link
			if url not in all_article_data.keys() and url not in bd_article_list:
				valid_article = True
				# skip invalid articles
				for keyword in list_skip_urls:
					if keyword in url:
						valid_article = False
						# break if found keyword
						break
				if valid_article is True:
					all_article_data[url] = category

def _handeling_failed_articles(query):
	"""
	Handles try and catch for faild articles for puching it into db
	"""
	try:
		pass
	except Exception as e:
		print("failed to insert query ==> %s" %(query))

# stores links from main source page
all_links = _get_links(source_page)

# filter out the link for catogary
for link in all_links:
	# links present on the page are either .cms format or page link with website
	# we need links within website so eliminate .cms links
	if '.cms' not in link and link[0] is '/':
		if '/weather/city' not in link and '/videos' not in link:
			categories.append(link)

categories = _filter_out_category(categories)

print("No of catogaries " + str(len(categories)))

category_threads = []
# get .cms links from catagory and store it
for category in categories:
	t = threading.Thread(target=_scan_and_push_category, args=(category,))
	category_threads.append(t)
	t.start()

# join all threads
for t in category_threads:
	t.join()

print("no of unique articles" + str(len(all_article_data)))

for url in all_article_data.keys():
	try:
		_filter_and_push_article(url,all_article_data[url])
	except Exception as e:
		print("Failed to add : "+url)
		print(e)

		created_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		query_string = "INSERT INTO failed_news (url,created_date,error) "
		values = 'values("%s","%s","%s")' %(url,created_date,"unknown")

		if "failed with 404 Client Error" in str(e):
			not_found_404 = not_found_404 + 1
			values = 'values("%s","%s","%s")' %(url,created_date,"404 Error")
			_handeling_failed_articles(query_string + values)
		elif "Duplicate entry" in str(e):
			duplicate_entry = duplicate_entry + 1
		elif "Incorrect string value" in str(e):
			values = 'values("%s","%s","%s")' %(url,created_date,"Incorrect string value")
			fail_count = fail_count + 1
			_handeling_failed_articles(query_string + values)
		else:
			fail_count = fail_count + 1
			_handeling_failed_articles(query_string + values)


print("no of unique articles=" + str(len(all_article_data)))

print("no of articals added=" + str(article_added))

print("no of failed articles=" + str(fail_count))

print("no of dups articles=" + str(duplicate_entry))

print("no of 404 articles=" + str(not_found_404))

print(datetime.datetime.now() - tm_st)

# data_point = {'added':str(article_added),
# 			'failed':str(fail_count),
# 			'404_error':str(not_found_404),
# 			'time_taken':str(datetime.datetime.now() - tm_st)}

# db.insert_into_influx()




