

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

# define datetime for last itteration sheduled
last_itteration = datetime.datetime.now() - datetime.timedelta(hours=1)

# start time of the script
tm_st = datetime.datetime.now()

# dict to save all the unique article
all_article_data = {}


# databse oblject
db = Database()
# retuens all the articles from added and failed
bd_article_list = db.get_all_article_url()

# Counter to trace the articles
article_added=0
fail_count = 0
not_found_404 = 0
duplicate_entry = 0

def _get_links(source):
	"""
	Finds all possible links present on perticular page
	returns list of all href
	"""
	# reques to main source and get the content
	page = requests.get(source, timeout=60, verify=True)
	webpage = html.fromstring(page.content)

	# finds the list of all link presnt on main source page
	links = webpage.xpath('//a/@href')

	return(links)

def _filter_and_push_article(source, category):
	"""
	filters out the artical according to date
	pushes the data in db if artical is not old
	data pushed:
		1. title
		2. date
		3. keywords
		4. summary
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
	# nlp will do get all the requied data link title, summary, keywords etc
	article.nlp()

	# query to insert the artile news
	query_string = "INSERT INTO News (url,title,created_date,summary,keywords,category,location,image) "

	# remove the unneccessary quotes
	title = article.title.replace('"',"'").replace("“","'").replace("”","'")
	# genetate the created data in required Mysql format
	created_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	# remove the unneccessary quotes and next line
	summary = article.summary.replace('\n',' ').replace('"',"'").replace("“","'").replace("”","'")
	# if the summay is more than 500 words truncate the summary to 500 words
	if len(summary) > 499:
		summary = summary[:499]

	# if summary and title are empty then the article failed to get the requred data
	# add this article in failed table for later use
	# also return if this case happens
	if summary is "" or title is "" :
		query_string_issue = "INSERT INTO failed_news (url,created_date,error) "
		values = 'values("%s","%s","%s")' %(source, created_date, 
			"NO Summary and Tile found")
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
	# Add values and generate the string for query
	values = 'values("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")' %(source,title,created_date,summary,keywords,category,location,image)

	print(query_string + values)

	# push into db
	db.query(query_string + values)
	# after pushing inc the counter for added article
	article_added = article_added+1
	print(article_added)


other_link = []

def _filter_and_push_category(category):
	#print(category)
	source = source_page + category
	cms_links = _get_links(source)
	for link in cms_links:
		# filter .cms link
		if '.cms' in link:
			url = link
			# add source page url if not present
			if link[0] is '/':
				url = source_page + link
			if 'http' not in link:
				url = source_page + link
			if url not in all_article_data.keys() and url not in bd_article_list:
				if '/weather/city' not in url:
					all_article_data[url] = category
				# _filter_and_push_article(url,category)

# Times of inda is the main source page
source_page = 'https://timesofindia.indiatimes.com/'

# stores all catogary
categories = []
# stores links from main source page
all_links = _get_links(source_page)

# filter out the link for catogary
for link in all_links:
	# links present on the page are either .cms format or page link with website
	# we need links within website so eliminate .cms links
	if '.cms' not in link and link[0] is '/':
		categories.append(link)


print("No of catogaries" + str(len(categories)))
category_threads = []
# get .cms links from catagory and store it
for category in categories:
	#_filter_and_push_category(category)
	t = threading.Thread(target=_filter_and_push_category, args=(category,))
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
			db.query(query_string + values)
		elif "Duplicate entry" in str(e):
			duplicate_entry = duplicate_entry + 1
		elif "Incorrect string value" in str(e):
			values = 'values("%s","%s","%s")' %(url,created_date,"Incorrect string value")
			fail_count = fail_count + 1
			db.query(query_string + values)
		else:
			fail_count = fail_count + 1
			db.query(query_string + values)


print("no of unique articles=" + str(len(all_article_data)))

print("no of articals added=" + str(article_added))

print("no of failed articles=" + str(fail_count))

print("no of dups articles=" + str(duplicate_entry))

print("no of 404 articles=" + str(not_found_404))

print(datetime.datetime.now() - tm_st)




