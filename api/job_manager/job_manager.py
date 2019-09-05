

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
from google_images_download import google_images_download
import MySQLdb
from influxdb import InfluxDBClient
import random

class Job_manager:
	global _db_connection
	global _db_cur
	global toi_image_default
	global all_article_data
	global categories
	global article_added
	global fail_count
	global not_found_404
	global duplicate_entry
	global source_page
	global list_skip_urls

	def __init__(self):
		"""
		Contructor creates connection object and cursor
		"""
		self._db_connection = MySQLdb.connect('localhost', 'root', '', 'news')
		self._db_connection.set_character_set('utf8')
		self._db_cur = self._db_connection.cursor()

		self.toi_image_default = "https://static.toiimg.com/thumb/msid-47529300,width-1070,height-580,imgsize-110164,resizemode-6,overlay-toi_sw,pt-32,y_pad-40/photo.jpg"

		# dict to save all the unique article
		self.all_article_data = {}

		# stores all catogary
		self.categories = []

		# Counter to trace the articles
		self.article_added=0
		self.fail_count = 0
		self.not_found_404 = 0
		self.duplicate_entry = 0

		# Times of inda is the main source page
		self.source_page = 'https://timesofindia.indiatimes.com/'

		# list of all unwanted urls keywords
		self.list_skip_urls = [
		'/photogallery',
		'/video',
		'/rss.cms',
		'/navbharattimes',
		'/weather',
		'/citizen-reporter',
		'/m.'
		]

	def query(self, query ):
		"""
		input required : query
		function:
		- executes query through cursor object
		- commits the data
		- returns the commited data in bunch
		"""
		result = self._db_cur.execute(query)
		self._db_connection.commit()
		return self._db_cur.fetchall()

	def query_fetchone(self, query ):
		"""
		input required : query
		function:
		- executes query through cursor object
		- commits the data
		- returns the commited data (a single row)
		"""
		result = self._db_cur.execute(query)
		self._db_connection.commit()
		return self._db_cur.fetchone()

	def get_all_article_url(self):
		"""
		Gives list all the article urls form News and failed_new table
		this is used to find the news which are newly added
		and skip the one which are already there
		saves lot of time
		"""

		tables = ['News', 'failed_news']
		all_articles = []

		for table in tables:
			query_string = "SELECT URL FROM " + table
			self._db_cur.execute(query_string)
			rows = self._db_cur.fetchall()
			for row in rows:
				all_articles.append(row[0])

		return all_articles

	def insert_into_influx(self, data):
		"""
		Will push all analysis data into influxdb
		this data will be used for ploting graphs
		Input: dict
		"""
		client = InfluxDBClient('localhost',
								'8086',
								'newsapi',
								'newsapi',
								'monitor_newsapi')
		data_point = [{"measurement":"per_hr_data",
					"fields": data
					}]
		client.write_points(data_point)

	def __del__(self):
		self._db_connection.close()

	def get_links(self, source):
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

	def get_image(self, title):
		"""
		Searches for the single image
		Input: keywords
		Output: returns single image path
		"""
		keywords = title.replace(",","")
		arguments = {"keywords": keywords,
					"limit":5,
					"format": "jpg",
					"no_download":True}

		response = google_images_download.googleimagesdownload()
		path = response.download(arguments)

		# path is tuple so path[0]
		# path[0][title] is dict for key as title and list_of image as value
		# path[0][title][0] to pick first image from list
		return (path[0][keywords][random.choice([0,1,2,3])])

	def check_image_path(self, image, title):
		"""
		Check the image path url if absent finds new one
		input: image_path, title
		output: returns valid image path
		"""
		r = requests.head(image)
		if r.status_code == requests.codes.ok:
			return image
		else:
			return self.get_image(title)

	def filter_and_push_article(self, source, category):
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
		# if the summay is more than 200 words use summary
		if len(text) > 250:
			text = article.summary.replace('\n',' ').replace('"',"'").replace("“","'").replace("”","'")
		# if the summay is more than 5000 words truncate the text to 500 words
		if len(text) > 5000:
			text = text[:4999]

		# if text and title are empty then the article failed to get the requred data
		# add this article in failed table for later use
		# also return if this case happens
		if text == "" or title == "" :
			query_string_issue = "INSERT INTO failed_news (url,created_date,error) "
			values = 'values("%s","%s","%s")' %(source, created_date, 
				"NO text and Tile found")
			self.query(query_string + values)
			self.fail_count == self.fail_count + 1
			return
		if len(text) < 50:
			query_string_issue = "INSERT INTO failed_news (url,created_date,error) "
			values = 'values("%s","%s","%s")' %(source, created_date,
				"Text filed less than 50")
			self.query(query_string + values)
			self.fail_count == self.fail_count + 1
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
		if image == self.toi_image_default:
			image = self.get_image(title)

		# check image path
		image = self.check_image_path(image, title)

		# Add values and generate the string for query
		values = 'values("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")' %(source,title,created_date,text,keywords,category,location,image)

		print(query_string + values)

		# push into db
		self.query(query_string + values)
		# after pushing inc the counter for added article
		self.article_added = self.article_added+1
		print(self.article_added)

	def filter_out_category(self, categories_raw):
		# intilize a null list
		unique_list = []

		# traverse for all elements
		for category in categories_raw:
			# check if exists in unique_list or not
			if category not in unique_list and len(category) > 1:
				unique_list.append(category)
		return unique_list

	def scan_and_push_category(self, category, bd_article_list):
		#print(category)
		source = self.source_page + category
		cms_links = self.get_links(source)
		for link in cms_links:
			# filter .cms link
			# last 4 char should be alwas .cms
			if '.cms' in link[-4:]:
				url = link
				# add source page url if not present
				if link[0] is '/':
					url = self.source_page + link
				if 'http' not in link:
					url = self.source_page + link
				if url not in self.all_article_data.keys() and url not in bd_article_list:
					valid_article = True
					# skip invalid articles
					for keyword in self.list_skip_urls:
						if keyword in url:
							valid_article = False
							# break if found keyword
							break
					if valid_article is True:
						self.all_article_data[url] = category

	def handeling_failed_articles(self, query_str):
		"""
		Handles try and catch for faild articles for puching it into db
		"""
		try:
			# push into db
			self.query(query_str)
		except Exception as e:
			print("failed to insert query ==> %s" %(query))

	def add_news(self):
		# start time of the script
		tm_st = datetime.datetime.now()
		# stores links from main source page
		all_links = self.get_links(self.source_page)

		# filter out the link for catogary
		for link in all_links:
			# links present on the page are either .cms format or page link with website
			# we need links within website so eliminate .cms links
			if '.cms' not in link and link[0] is '/':
				if '/weather/city' not in link and '/videos' not in link:
					self.categories.append(link)

		self.categories = self.filter_out_category(self.categories)

		print("No of catogaries " + str(len(self.categories)))

		# retuens all the articles from added and failed
		bd_article_list = self.get_all_article_url()

		category_threads = []
		# get .cms links from catagory and store it
		for category in self.categories:
			t = threading.Thread(target=self.scan_and_push_category, args=(category,bd_article_list,))
			category_threads.append(t)
			t.start()

		# join all threads
		for t in category_threads:
			t.join()

		print("no of unique articles" + str(len(self.all_article_data)))

		for url in self.all_article_data.keys():
			try:
				self.filter_and_push_article(url,self.all_article_data[url])
			except Exception as e:
				print("Failed to add : "+url)
				print(e)

				created_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				query_string = "INSERT INTO failed_news (url,created_date,error) "
				values = 'values("%s","%s","%s")' %(url,created_date,"unknown")

				if "failed with 404 Client Error" in str(e):
					self.not_found_404 = self.not_found_404 + 1
					values = 'values("%s","%s","%s")' %(url,created_date,"404 Error")
					self.handeling_failed_articles(query_string + values)
				elif "Duplicate entry" in str(e):
					self.duplicate_entry = self.duplicate_entry + 1
					values = 'values("%s","%s","%s")' %(url,created_date,"Duplicate entry")
					self.handeling_failed_articles(query_string + values)
				elif "Incorrect string value" in str(e):
					values = 'values("%s","%s","%s")' %(url,created_date,"Incorrect string value")
					self.fail_count = self.fail_count + 1
					self.handeling_failed_articles(query_string + values)
				else:
					self.fail_count = self.fail_count + 1
					self.handeling_failed_articles(query_string + values)


		print("no of unique articles=" + str(len(self.all_article_data)))

		print("no of articals added=" + str(self.article_added))

		print("no of failed articles=" + str(self.fail_count))

		print("no of dups articles=" + str(self.duplicate_entry))

		print("no of 404 articles=" + str(self.not_found_404))

		print(datetime.datetime.now() - tm_st)

		data_point = {'added':str(self.article_added),
					'failed':str(self.fail_count),
					'404_error':str(self.not_found_404),
					'time_taken':str(datetime.datetime.now() - tm_st)}

		self.insert_into_influx(data_point)

def start_scan():
	jb = Job_manager()
	jb.add_news()



