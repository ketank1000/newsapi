from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from job_manager import job_manager

def start():
	scheduler = BackgroundScheduler()
	scheduler.add_job(job_manager.start_scan, 'interval', minutes=30)
	scheduler.start()