import json
from django.test import TestCase
from django.db import connection
from curious import model_registry
from curious_tests.models import Blog, Entry
import curious_tests.models

class TestBatchFetch(TestCase):
  N = 20

  def setUp(self):
    blog = Blog(name='Databases')
    blog.save()
    self.blog = blog

    headlines = ['MySQL is a relational DB']*TestBatchFetch.N
    self.entries = [Entry(headline=headline, blog=blog) for i, headline in enumerate(headlines)]
    for entry in self.entries:
      entry.save()

    # register model
    if len(model_registry.model_names) == 0:
      model_registry.register(curious_tests.models)
      model_registry.add_custom_rel('Blog', 'authors')

  def test_fetch_objects_and_related_objects(self):
    data = dict(ids=[e.id for e in self.entries])
    r = self.client.post('/curious/models/Entry/', data=json.dumps(data), content_type='application/json')
    self.assertEquals(r.status_code, 200)
    results = json.loads(r.content)['result']
    self.assertEquals(results['fields'], ["id", "blog_id", "headline", "response_to_id"])
    self.assertItemsEqual(results['objects'],
                          [[None, # url
                            e.id,
                            [self.blog.__class__.__name__, self.blog.pk, self.blog.name, None],
                            e.headline,
                            None]
                           for e in self.entries])
