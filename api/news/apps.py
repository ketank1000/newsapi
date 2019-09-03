from django.apps import AppConfig


class NewsConfig(AppConfig):
    name = 'news'

    def ready(self):
        from job_manager import update
        update.start()