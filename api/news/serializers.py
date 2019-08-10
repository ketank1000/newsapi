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
	return : id, url, title, summary, created_date, image
	"""

	# overides the serilized data from model
	# Used from translating the title and summay to given lang
	title = serializers.SerializerMethodField()
	summary = serializers.SerializerMethodField()

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

	def get_summary(self, obj):
		"""
		Method filed to translate to given lang for summary
		"""
		lang = self.context.get('lang')
		if (lang is not 'en'):
			translator = Translator(service_urls=[
				'translate.google.com',
				'translate.google.co.kr',
			])
			translation = translator.translate(obj.summary, dest=lang)
			return translation.text
		else:
			return obj.summary

	class Meta:
		model = News
		fields = ('id','url','title','summary','created_date','image')
		# fields = '__all__'

class failed_newsSerializer(serializers.ModelSerializer):
	"""
	Serilizer for getting faild news
	"""
	class Meta:
		model = failed_news
		fields = '__all__'