from django.test import TestCase
from curious import model_registry
from curious.query import Query
from curious_tests.models import Blog, Entry, Author
from curious_tests import assertQueryResultsEqual
import curious_tests.models

class TestQueryFkToSelf(TestCase):

  def setUp(self):
    blog = Blog(name='Databases')
    blog.save()
    self.blog = blog

    authors = ('John Smith', 'Jane Doe', 'Joe Plummer', 'Jessical Jones')
    headlines = ('MySQL is a good relational DB',
                 'Postgres is a really good relational DB',
                 'Neo4J is a graph DB',
                 'But we are not comparing relational and graph DBs')

    self.entries = [Entry(headline=headline, blog=blog) for headline in headlines]
    for entry in self.entries:
      entry.save()

    self.entries[1].response_to = self.entries[0]
    self.entries[1].save()
    self.entries[2].response_to = self.entries[1]
    self.entries[2].save()
    self.entries[3].response_to = self.entries[2]
    self.entries[3].save()

    self.authors = [Author(name=name, age=30) for name in authors]
    for i, author in enumerate(self.authors):
      author.save()

    for i, entry in enumerate(self.entries):
      entry.authors.add(self.authors[i])

    model_registry.register(curious_tests.models)
    
  def tearDown(self):
    model_registry.clear()

  def test_fk_to_self(self):
    qs = 'Blog(%s) Blog.entry_set(headline__icontains="Postgres") Entry.response_to' % self.blog.pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0],
                            [(self.entries[0], None)])
    self.assertEquals(result[1], Entry)

  def test_join_fk_to_self(self):
    qs = 'Blog(%s) Blog.entry_set(headline__icontains="Postgres"), Entry.response_to' % self.blog.pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.entries[1], None)])
    self.assertEquals(result[0][1][1], 0)
    assertQueryResultsEqual(self, result[0][1][0], [(self.entries[0], self.entries[1].pk)])
    self.assertEquals(result[1], Entry)

  def test_reverse_of_fk_to_self(self):
    qs = 'Blog(%s) Blog.entry_set(headline__icontains="Postgres") Entry.responses' % self.blog.pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0],
                            [(self.entries[2], None)])
    self.assertEquals(result[1], Entry)

  def test_join_reverse_of_fk_to_self(self):
    qs = 'Blog(%s) Blog.entry_set(headline__icontains="Postgres"), Entry.responses' % self.blog.pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.entries[1], None)])
    self.assertEquals(result[0][1][1], 0)
    assertQueryResultsEqual(self, result[0][1][0], [(self.entries[2], self.entries[1].pk)])
    self.assertEquals(result[1], Entry)
