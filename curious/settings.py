from django.conf import settings

DEBUG = getattr(settings, 'CURIOUS_DEBUG', False)
