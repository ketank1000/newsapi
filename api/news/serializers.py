from rest_framework import serializers
from . models import News, failed_news
from googletrans import Translator

class NewsSerializer(serializers.ModelSerializer):
	"""
	Serilizer function to serilize News article
	Input:
		- lang: language to translate to
				(defalut english)
	returns the data in API and JSON format
	translates to given language
	return : id, url, title, text, created_date, image
	"""

	# overides the serilized data from model
	# Used from translating the title and text to given lang
	title = serializers.SerializerMethodField()
	text = serializers.SerializerMethodField()

	def get_title(self, obj):
		"""
		Method filed to translate to given lang for title
		"""
		lang = self.context.get('lang')
		if (lang is not 'en'):
			translator = Translator(service_urls=[
				'translate.google.com',
				'translate.google.co.kr',
			])
			translation = translator.translate(obj.title, dest=lang)
			return translation.text
		else:
			return obj.title

	def get_text(self, obj):
		"""
		Method filed to translate to given lang for text
		"""
		lang = self.context.get('lang')
		if (lang is not 'en'):
			translator = Translator(service_urls=[
				'translate.google.com',
				'translate.google.co.kr',
			])
			translation = translator.translate(obj.text, dest=lang)
			return translation.text
		else:
			return obj.text

	class Meta:
		model = News
		fields = ('id','url','title','text','created_date','image','category')
		# fields = '__all__'

class failed_newsSerializer(serializers.ModelSerializer):
	"""
	Serilizer for getting faild news
	"""
	class Meta:
		model = failed_news
		fields = '__all__'