from django.test import TestCase
from curious import model_registry
from curious.query import Query
from curious_tests.models import Blog, Entry, Author, Comment
from curious_tests import assertQueryResultsEqual
import curious_tests.models

class TestSubQueries(TestCase):

  def setUp(self):
    blog = Blog(name='Databases')
    blog.save()
    self.blogs = [blog]

    authors = ('John Smith', 'Jane Doe', 'Joe Plummer')
    headlines = ('MySQL is a relational DB',
                 'Postgres is a really good relational DB',
                 'Neo4J is a graph DB')

    self.entries = [Entry(headline=headline, blog=blog) for headline in headlines]
    for entry in self.entries:
      entry.save()

    self.authors = [Author(name=name) for name in authors]
    for author in self.authors:
      author.save()

    for i, entry in enumerate(self.entries):
      entry.authors.add(self.authors[i])
      entry.authors.add(self.authors[(i+1)%len(self.authors)])

    # register model
    model_registry.register(curious_tests.models)

  def tearDown(self):
    model_registry.clear()

  def test_or_queries(self):
    qs = 'Blog(%s) ' % self.blogs[0].pk +\
         '(Blog.entry_set(headline__icontains="MySQL")) | (Blog.entry_set(headline__icontains="Postgres")), '+\
         'Entry.authors'
    query = Query(qs)
    result = query()

    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.entries[0], None),
                                                    (self.entries[1], None)])

    self.assertEquals(result[0][1][1], 0)
    assertQueryResultsEqual(self, result[0][1][0], [(self.authors[0], self.entries[0].pk),
                                                    (self.authors[1], self.entries[0].pk),
                                                    (self.authors[1], self.entries[1].pk),
                                                    (self.authors[2], self.entries[1].pk)])
    self.assertEquals(len(result[0]), 2)
    self.assertEquals(result[1], Author)

  def test_joining_with_or_queries_at_the_end(self):
    qs = 'Blog(%s), ' % self.blogs[0].pk +\
         '(Blog.entry_set(headline__icontains="MySQL")) | (Blog.entry_set(headline__icontains="Postgres"))'
    query = Query(qs)
    result = query()

    self.assertEquals(len(result[0]), 2)

    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.blogs[0], None)])

    self.assertEquals(result[0][1][1], 0)
    assertQueryResultsEqual(self, result[0][1][0], [(self.entries[0], self.blogs[0].pk),
                                                    (self.entries[1], self.blogs[0].pk)])

    self.assertEquals(result[1], Entry)

  def test_joining_with_or_queries(self):
    qs = 'Blog(%s), ' % self.blogs[0].pk +\
         '(Blog.entry_set(headline__icontains="MySQL")) | (Blog.entry_set(headline__icontains="Postgres")), '+\
         'Entry.authors'
    query = Query(qs)
    result = query()

    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.blogs[0], None)])

    self.assertEquals(result[0][1][1], 0)
    assertQueryResultsEqual(self, result[0][1][0], [(self.entries[0], self.blogs[0].pk),
                                                    (self.entries[1], self.blogs[0].pk)])

    self.assertEquals(result[0][2][1], 1)
    assertQueryResultsEqual(self, result[0][2][0], [(self.authors[0], self.entries[0].pk),
                                                    (self.authors[1], self.entries[0].pk),
                                                    (self.authors[1], self.entries[1].pk),
                                                    (self.authors[2], self.entries[1].pk)])
    self.assertEquals(len(result[0]), 3)
    self.assertEquals(result[1], Author)

  def test_or_queries_matching_nothing(self):
    qs = 'Blog(%s), ' % self.blogs[0].pk +\
         '(Blog.entry_set(headline__icontains="Foo")) | (Blog.entry_set(headline__icontains="Bar")), '+\
         'Entry.authors'
    query = Query(qs)
    result = query()
    self.assertEquals(len(result[0]), 3)

    assertQueryResultsEqual(self, result[0][0][0], [(self.blogs[0], None)])
    self.assertEquals(result[0][1], ([], 0))
    self.assertEquals(result[0][2], ([], 1))
