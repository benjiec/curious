from django.conf.urls import include, url

urlpatterns = [
  url(r'^curious/', include('curious.urls')),
]
