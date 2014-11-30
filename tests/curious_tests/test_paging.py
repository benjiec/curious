from django.test import TestCase
from curious import model_registry
from curious.query import Query
from curious_tests.models import Blog, Entry, Author
from curious_tests import assertQueryResultsEqual
import curious_tests.models

class TestPaging(TestCase):

  def setUp(self):
    self.blogs = [Blog(name='A'),
                  Blog(name='C'),
                  Blog(name='B')]
    for b in self.blogs:
      b.save()

    headlines = ('A entry', 'C entry', 'B entry')
    self.entries = [Entry(headline=headline, blog=self.blogs[i]) for i, headline in enumerate(headlines)]
    for entry in self.entries:
      entry.save()

    model_registry.register(curious_tests.models)

  def tearDown(self):
    model_registry.clear()

  def test_first(self):
    qs = 'Blog(id__isnull=False).first(2)'
    query = Query(qs)
    result = query()
    assertQueryResultsEqual(self, result[0][0][0],
                            [(self.blogs[0], None), (self.blogs[1], None)])

  def test_last(self):
    qs = 'Blog(id__isnull=False).last(2)'
    query = Query(qs)
    result = query()
    assertQueryResultsEqual(self, result[0][0][0],
                            [(self.blogs[2], None), (self.blogs[1], None)])

  def test_order_first(self):
    qs = 'Blog(id__isnull=False).order(name).first(2)'
    query = Query(qs)
    result = query()
    assertQueryResultsEqual(self, result[0][0][0],
                            [(self.blogs[0], None), (self.blogs[2], None)])
  
  def test_order_last(self):
    qs = 'Blog(id__isnull=False).order(name).last(2)'
    query = Query(qs)
    result = query()
    assertQueryResultsEqual(self, result[0][0][0],
                            [(self.blogs[1], None), (self.blogs[2], None)])

  def test_order_start(self):
    qs = 'Blog(id__isnull=False).order(name).start(1)'
    query = Query(qs)
    result = query()
    assertQueryResultsEqual(self, result[0][0][0],
                            [(self.blogs[2], None), (self.blogs[1], None)])

  def test_order_start_limit(self):
    qs = 'Blog(id__isnull=False).order(name).start(1).limit(1)'
    query = Query(qs)
    result = query()
    assertQueryResultsEqual(self, result[0][0][0],
                            [(self.blogs[2], None)])

  def test_page_then_get_related(self):
    qs = 'Blog(id__isnull=False).order(name).first(2), Blog.entry_set'
    query = Query(qs)
    result = query()
    assertQueryResultsEqual(self, result[0][0][0],
                            [(self.blogs[0], None), (self.blogs[2], None)])
    assertQueryResultsEqual(self, result[0][1][0],
                            [(self.entries[0], 1), (self.entries[2], 3)])
