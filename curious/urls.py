from django.conf.urls import *
from django.views.generic.base import TemplateView
from django.http import HttpResponseRedirect
from .api import ObjectView, ModelView, ModelListView, QueryView

def redirect_to_static(request):
  path = request.get_full_path()
  return HttpResponseRedirect('/static%s' % path)

urlpatterns = patterns('',
  url(r'^objects/(?P<model_name>[\w\-]+)/(?P<id>[\w\-]+)/$', ObjectView.as_view()),
  url(r'^models/(?P<model_name>[\w\-]+)/$', ModelView.as_view()),
  url(r'^models/$', ModelListView.as_view()),
  url(r'^q/$', QueryView.as_view()),

  # sometimes you need to get to the curious query page via Django, e.g. to
  # work with authentication. here we serve the curious.html via Django
  # template engine, and add redirects for relative URLs so they match the
  # curious/static directory tree.
  url(r'^$', TemplateView.as_view(template_name='curious/curious.html'), name='curious'),
  url(r'^dist', redirect_to_static),
  url(r'^lib', redirect_to_static),
)
