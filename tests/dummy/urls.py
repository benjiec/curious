from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
  url(r'^curious/', include('curious.urls')),
)
