from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from job_manager import job_manager

def start():
	jb = job_manager.Job_manager()
	scheduler = BackgroundScheduler()
	scheduler.add_job(jb.add_news, 'interval', minutes=1)
	scheduler.start()