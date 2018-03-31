from django.test import TestCase, override_settings
from django.db import connection

import curious_tests.models
from curious import model_registry
from curious.related import remote_fk
from curious.query import Query
from curious_tests.models import Blog, Entry, Author


class TestRelated(TestCase):
  N = 20

  def setUp(self):
    self.blog = Blog(name='Databases')
    self.blog.save()

    self.entries = [Entry(headline='Abc {}'.format(i), blog=self.blog) for i in xrange(self.N)]
    for index, entry in enumerate(self.entries):
      if index < len(self.entries) - 1:
        entry.related_blog_id = self.entries[index + 1].pk

    for entry in self.entries:
      entry.save()

    self.query_count = len(connection.queries)
    model_registry.register(curious_tests.models)
    Blog.entry_ = remote_fk('entry_id', Entry)
    Entry.related_blog_ = remote_fk('related_blog_id', Entry)
    model_registry.get_manager('Entry').allowed_relationships = [
      'related_blog_',
    ]

  @override_settings(DEBUG=True)
  def test_reverse_lookup_in_one(self):
    qs = 'Blog(id={}), Blog.entry_set ?(Entry.related_blog_)'.format(self.blog.pk)
    query = Query(qs)
    result = query()
    self.assertEqual(len(connection.queries) - self.query_count, 4)
    self.assertEqual(len(result[0][1][0]), self.N)
