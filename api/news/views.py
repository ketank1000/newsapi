from django.shortcuts import render
from django.http import HttpResponse
from django.template import RequestContext, loader, Context
from django.shortcuts import render_to_response, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework import status
from . models import News, failed_news
from . serializers import NewsSerializer, failed_newsSerializer
from django.db.models import Q
from rest_framework.authtoken.models import Token

# Create your views here.

class newsfeed(APIView):
	"""
	Serilizer View to get get and post the data
	API used to get news feed
	"""
	# Authentication is done here through user token
	# authentication_classes = [SessionAuthentication, TokenAuthentication]
	# permission_classes = [IsAdminUser]
	def get(self, request):
		"""
		Get method for handling the request
		Input request:
			- city: list of cites
			- category: list of category
			- ids: list of ids to be excluded
			- lang: news in lang (defalut en)
			- qt: no articles to be requested (default 5)
		"""

		# get all request paremeter
		cities = self.request.query_params.getlist('city','')
		categories = self.request.query_params.getlist('category','')
		ids = self.request.query_params.getlist('ids','')
		# default lang is english
		lang = self.request.query_params.get('lang','en')
		# default no of articles to be send
		qt = int(self.request.query_params.get('qt',5))

		# create the default query
		condition = Q()

		# if the one city is given in the list
		if len(cities) > 0:
			condition = Q(category__icontains=cities[0])
			# if more then one city is given in the list
			if len(cities) > 1:
				for city in cities[1:]:
					condition |= Q(category__icontains=city)
					condition |= Q(keywords__icontains=city)

		# if one category is given in the list
		if len(categories) > 0:
			condition |= Q(category__icontains=categories[0])
			# if more then one category is given in the list
			if len(categories) > 1:
				for category in categories[1:]:
					condition |= Q(category__icontains=category)
					condition |= Q(keywords__icontains=category)

		# get the latest 100 articles from the generate condition
		news_list = News.objects.filter(condition).exclude(id__in=ids).order_by('-id')[:qt]

		# call the serilizer to serilize the data 
		# passing the context as lang for translation
		articles_list = NewsSerializer(news_list, many=True,context={'lang': lang})

		# return the serilize data
		return Response(articles_list.data)

	def post(self, request):
		"""
		Skip the post
		No posting data from the API
		"""
		pass