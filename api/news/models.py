from django.db import models

# Create your models here.


class News(models.Model):
	id = models.AutoField(primary_key=True)
	url = models.CharField(max_length=255,unique=True,null=False)
	title = models.CharField(max_length=200)
	summary = models.CharField(max_length=500)
	created_date = models.DateTimeField()
	keywords = models.CharField(max_length=200)
	category = models.CharField(max_length=200)
	location = models.CharField(max_length=50)
	image = models.CharField(max_length=200)

	# def __str__(self):
	# 	return self.url

	class Meta:
		db_table = 'News'


class failed_news(models.Model):
	id = models.AutoField(primary_key=True)
	url = models.CharField(max_length=255
		,unique=True,null=False)
	created_date = models.DateTimeField()
	error = models.CharField(max_length=500)

	def __str__(self):
		return self.url

	class Meta:
		db_table = 'failed_news'
