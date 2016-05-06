from django.test import TestCase
from django.db import connection, reset_queries
from curious.graph import traverse
from curious_tests.models import Blog, Entry, Author

class TestQueryCount(TestCase):
  N = 20

  def setUp(self):
    self.blogs = [Blog(name='Databases'), Blog(name='More Databases')]
    for blog in self.blogs:
      blog.save()

    authors = ['John Smith']*TestQueryCount.N
    headlines = ['MySQL is a relational DB']*TestQueryCount.N

    self.entries = [Entry(headline=headline, blog=self.blogs[i%2]) for i, headline in enumerate(headlines)]
    for entry in self.entries:
      entry.save()

    self.authors = [Author(name=name) for name in authors]
    for author in self.authors:
      author.save()

    for i, entry in enumerate(self.entries):
      entry.authors.add(self.authors[i])
      entry.authors.add(self.authors[(i+1)%len(self.authors)])

  def test_single_query_for_M2M(self):
    connection.use_debug_cursor = True
    reset_queries()
    authors = traverse(self.entries, Entry.authors)
    self.assertEquals(len(authors), 2*TestQueryCount.N)
    self.assertEquals(len(connection.queries), 1)

  def test_single_query_for_M2M_with_filter(self):
    connection.use_debug_cursor = True
    reset_queries()
    f = dict(method='filter', kwargs=dict(name__icontains='Smith'))
    authors = traverse(self.entries, Entry.authors, filters=[f])
    self.assertEquals(len(authors), 2*TestQueryCount.N)
    self.assertEquals(len(connection.queries), 1)

  def test_single_query_for_reverse_M2M(self):
    connection.use_debug_cursor = True
    reset_queries()
    entries = traverse(self.authors, Author.entry_set)
    self.assertEquals(len(entries), 2*TestQueryCount.N)
    self.assertEquals(len(connection.queries), 1)

  def test_single_query_for_FK(self):
    connection.use_debug_cursor = True
    reset_queries()
    blogs = traverse(self.entries, Entry.blog)
    self.assertEquals(len(blogs), TestQueryCount.N)
    self.assertEquals(len(connection.queries), 1)

  def test_single_query_for_reverse_FK(self):
    connection.use_debug_cursor = True
    reset_queries()
    entries = traverse(self.blogs, Blog.entry_set)
    self.assertEquals(len(entries), TestQueryCount.N)
    self.assertEquals(len(connection.queries), 1)
