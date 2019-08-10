from django.contrib import admin
from . models import News, failed_news

# Register your models here.
admin.site.register(News)
admin.site.register(failed_news)
