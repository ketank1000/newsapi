
toi_image_default = "https://static.toiimg.com/thumb/msid-47529300,width-1070,height-580,imgsize-110164,resizemode-6,overlay-toi_sw,pt-32,y_pad-40/photo.jpg"

# start time of the script
tm_st = datetime.datetime.now()

# dict to save all the unique article
all_article_data = {}

# stores all catogary
categories = []

# Counter to trace the articles
article_added=0
fail_count = 0
not_found_404 = 0
duplicate_entry = 0

# Times of inda is the main source page
source_page = 'https://timesofindia.indiatimes.com/'

# list of all unwanted urls keywords
list_skip_urls = [
'/photogallery',
'/video/',
'/rss.cms',
'/navbharattimes'
]