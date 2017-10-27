from curious import deferred_to_real
from django.test import TestCase, override_settings
from django.db import connection
from curious_tests.models import Blog, Entry

class TestDeferredToReal(TestCase):

  def setUp(self):
    blog = Blog(name='Databases')
    blog.save()
    self.blogs = [blog]

    headlines = ('MySQL is a relational DB',
                 'Postgres is a really good relational DB',
                 'Neo4J is a graph DB')

    self.entries = [Entry(headline=headline, blog=blog) for headline in headlines]
    for entry in self.entries:
      entry.save()

    self.query_count = len(connection.queries)

  def test_converts_deferred_objects_to_real_objects(self):
    entries = list(Entry.objects.all().filter(blog__name='Databases').only('id'))
    self.assertEquals(len(entries), 3)
    # test objects are deferred
    for entry in entries:
      self.assertEquals('id' in entry.__dict__, True)
      self.assertEquals('headline' in entry.__dict__, False)

    # convert to real
    entries = deferred_to_real(entries)
    self.assertEquals(len(entries), 3)
    for entry in entries:
      self.assertEquals('id' in entry.__dict__, True)
      self.assertEquals('headline' in entry.__dict__, True)

  def test_conversion_uses_single_query(self):
    # We have to prefix with .all() to prevent the object cache from returning complete
    # objects from previous queries
    entries = list(Entry.objects.all().filter(blog__name='Databases').only('id'))
    with override_settings(DEBUG=True):
      entries = list(deferred_to_real(entries))
      self.assertEquals(len(connection.queries) - self.query_count, 1)

  def test_converts_mixture_of_deferred_and_real_objects(self):
    real_entries = list(Entry.objects.all().filter(blog__name='Databases'))
    self.assertEquals(len(real_entries), 3)
    # test objects are real
    for entry in real_entries:
      self.assertEquals('id' in entry.__dict__, True)
      self.assertEquals('headline' in entry.__dict__, True)

    deferred_entries = list(Entry.objects.all().filter(blog__name='Databases').only('id'))
    self.assertEquals(len(deferred_entries), 3)
    # test objects are deferred
    for entry in deferred_entries:
      self.assertEquals('id' in entry.__dict__, True)
      self.assertEquals('headline' in entry.__dict__, False)

    # convert to real and uniquefy
    entries = deferred_to_real(real_entries+deferred_entries)
    self.assertEquals(len(entries), 3)
    for entry in entries:
      self.assertEquals('id' in entry.__dict__, True)
      self.assertEquals('headline' in entry.__dict__, True)
