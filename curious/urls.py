from django.conf.urls import *
from .api import ObjectView, ModelView, ModelListView, QueryView

urlpatterns = patterns('',
  url(r'^objects/(?P<model_name>[\w\-]+)/(?P<id>[\w\-]+)/$', ObjectView.as_view()),
  url(r'^models/(?P<model_name>[\w\-]+)/$', ModelView.as_view()),
  url(r'^models/$', ModelListView.as_view()),
  url(r'^q/$', QueryView.as_view()),
)
