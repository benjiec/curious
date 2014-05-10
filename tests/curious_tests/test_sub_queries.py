from django.test import TestCase
from curious import model_registry
from curious.query import Query
from curious_tests.models import Blog, Entry, Author
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
    if len(model_registry.model_names) == 0:
      model_registry.register(curious_tests.models)
      model_registry.add_custom_rel('Blog', 'authors')

  def test_join_queries(self):
    qs = 'Blog(%s) Blog.entry_set, Entry.authors' % self.blogs[0].pk
    query = Query(qs)
    result = query()
    assertQueryResultsEqual(self, result[0][0], [(self.entries[0], self.blogs[0].pk),
                                                 (self.entries[1], self.blogs[0].pk),
                                                 (self.entries[2], self.blogs[0].pk)])
    assertQueryResultsEqual(self, result[0][1], [(self.authors[0], self.entries[0].pk),
                                                 (self.authors[1], self.entries[0].pk),
                                                 (self.authors[1], self.entries[1].pk),
                                                 (self.authors[2], self.entries[1].pk),
                                                 (self.authors[2], self.entries[2].pk),
                                                 (self.authors[0], self.entries[2].pk)])
    self.assertEquals(len(result[0]), 2)
    self.assertEquals(result[1], Author)

  def test_filtering_queries(self):
    qs = 'Blog(%s) (Blog.entry_set) Blog.entry_set' % self.blogs[0].pk
    query = Query(qs)
    result = query()
    assertQueryResultsEqual(self, result[0][0], [(self.blogs[0], self.blogs[0].pk)])
    assertQueryResultsEqual(self, result[0][1], [(self.entries[0], self.blogs[0].pk),
                                                 (self.entries[1], self.blogs[0].pk),
                                                 (self.entries[2], self.blogs[0].pk)])
    assertQueryResultsEqual(self, result[0][2], [(self.entries[0], self.entries[0].pk),
                                                 (self.entries[1], self.entries[0].pk),
                                                 (self.entries[2], self.entries[0].pk),
                                                 (self.entries[0], self.entries[1].pk),
                                                 (self.entries[1], self.entries[1].pk),
                                                 (self.entries[2], self.entries[1].pk),
                                                 (self.entries[0], self.entries[2].pk),
                                                 (self.entries[1], self.entries[2].pk),
                                                 (self.entries[2], self.entries[2].pk)])
    self.assertEquals(len(result[0]), 3)
    self.assertEquals(result[1], Entry)

  def test_filtering_queries_without_join(self):
    qs = 'Blog(%s) +(Blog.entry_set) Blog.entry_set' % self.blogs[0].pk
    query = Query(qs)
    result = query()
    assertQueryResultsEqual(self, result[0][0], [(self.entries[0], self.blogs[0].pk),
                                                 (self.entries[1], self.blogs[0].pk),
                                                 (self.entries[2], self.blogs[0].pk)])
    self.assertEquals(len(result[0]), 1)
    self.assertEquals(result[1], Entry)

  def test_filtering_queries_negatively_without_join(self):
    qs = 'Blog(%s) -(Blog.entry_set) Blog.entry_set' % self.blogs[0].pk
    query = Query(qs)
    result = query()
    self.assertEquals(result, ([], None))
