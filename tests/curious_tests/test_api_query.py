import json
from django.test import TestCase
from django.db import connection
from curious import model_registry
from curious.api import ModelView
from curious_tests.models import Blog, Entry
import curious_tests.models

class TestQueryAPI(TestCase):
  N = 3

  def setUp(self):
    blog = Blog(name='Databases')
    blog.save()
    self.blog = blog

    headlines = ['MySQL is a relational DB']*TestQueryAPI.N
    self.entries = [Entry(headline=headline, blog=blog) for i, headline in enumerate(headlines)]
    for entry in self.entries:
      entry.save()

    # register model
    if len(model_registry.model_names) == 0:
      model_registry.register(curious_tests.models)

  def test_query(self):
    r = self.client.get('/curious/q/', dict(q='Blog(%s) Blog.entry_set' % self.blog.pk))
    self.assertEquals(r.status_code, 200)
    j = json.loads(r.content)
    self.assertEquals(j.keys(), ['result'])
    self.assertEquals(j['result']['last_model'], 'Entry')
    self.assertEquals(len(j['result']['results']), 1)
    self.assertItemsEqual(j['result']['results'][0].keys(), ['model', 'join_index', 'objects'])
    self.assertEquals(j['result']['results'][0]['model'], 'Entry')
    self.assertEquals(j['result']['results'][0]['join_index'], -1)
    objects = [[obj.id, None] for obj in self.entries]
    self.assertItemsEqual(j['result']['results'][0]['objects'], objects)

  def test_join_query(self):
    r = self.client.get('/curious/q/', dict(q='Blog(%s), Blog.entry_set' % self.blog.pk))
    self.assertEquals(r.status_code, 200)
    j = json.loads(r.content)
    self.assertEquals(j.keys(), ['result'])
    self.assertEquals(j['result']['last_model'], 'Entry')
    self.assertEquals(len(j['result']['results']), 2)

    self.assertItemsEqual(j['result']['results'][0].keys(), ['model', 'join_index', 'objects'])
    self.assertEquals(j['result']['results'][0]['model'], 'Blog')
    self.assertEquals(j['result']['results'][0]['join_index'], -1)
    self.assertItemsEqual(j['result']['results'][0]['objects'], [[self.blog.pk, None]])

    self.assertItemsEqual(j['result']['results'][1].keys(), ['model', 'join_index', 'objects'])
    self.assertEquals(j['result']['results'][1]['model'], 'Entry')
    self.assertEquals(j['result']['results'][1]['join_index'], 0)
    objects = [[obj.id, self.blog.pk] for obj in self.entries]
    self.assertItemsEqual(j['result']['results'][1]['objects'], objects)
  
  def test_getting_data_with_query(self):
    r = self.client.get('/curious/q/', dict(d=1, q='Blog(%s), Blog.entry_set' % self.blog.pk))
    self.assertEquals(r.status_code, 200)
    j = json.loads(r.content)
    self.assertEquals(j.keys(), ['result'])

    self.assertEquals(j['result']['last_model'], 'Entry')
    self.assertEquals(len(j['result']['results']), 2)

    self.assertItemsEqual(j['result']['results'][0].keys(), ['model', 'join_index', 'objects'])
    self.assertEquals(j['result']['results'][0]['model'], 'Blog')
    self.assertEquals(j['result']['results'][0]['join_index'], -1)
    self.assertItemsEqual(j['result']['results'][0]['objects'], [[self.blog.pk, None]])

    self.assertItemsEqual(j['result']['results'][1].keys(), ['model', 'join_index', 'objects'])
    self.assertEquals(j['result']['results'][1]['model'], 'Entry')
    self.assertEquals(j['result']['results'][1]['join_index'], 0)
    objects = [[obj.id, self.blog.pk] for obj in self.entries]
    self.assertItemsEqual(j['result']['results'][1]['objects'], objects)

    self.assertItemsEqual(j['result'].keys(), ['last_model', 'results', 'computed_on', 'data'])
    self.assertEquals(j['result']['data'][0], ModelView.objects_to_dict([self.blog]))
    self.assertEquals(j['result']['data'][1], json.loads(json.dumps(ModelView.objects_to_dict(self.entries))))
