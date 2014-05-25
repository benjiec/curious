from django.test import TestCase
from curious import model_registry
from curious.query import Query
from curious_tests.models import Blog, Entry, Author
from curious_tests import assertQueryResultsEqual
import curious_tests.models

class TestQueryM2M(TestCase):

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

    for entry, author in zip(self.entries, self.authors):
      entry.authors.add(author)

    for i, author in enumerate(self.authors):
      author.friends.add(self.authors[(i+1)%len(self.authors)])

    # register model
    if len(model_registry.model_names) == 0:
      model_registry.register(curious_tests.models)

  def test_query_with_m2m_relationship(self):
    qs = 'Blog(%s) Blog.entry_set Entry.authors Author.friends' % self.blogs[0].pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0],
                            [
                              (self.authors[1], None),
                              (self.authors[2], None),
                              (self.authors[0], None),
                            ])
    self.assertEquals(result[1], Author)

  def test_join_m2m_relationship(self):
    # M2M relationship defined is symmetrical, which means if A is friend of B,
    # B is also friend of A. Below asserts check this assumption.
    self.assertItemsEqual(self.authors[0].friends.all(), [self.authors[1], self.authors[2]])
    self.assertItemsEqual(self.authors[1].friends.all(), [self.authors[0], self.authors[2]])
    self.assertItemsEqual(self.authors[2].friends.all(), [self.authors[0], self.authors[1]])

    qs = 'Blog(%s) Blog.entry_set Entry.authors, Author.friends' % self.blogs[0].pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0],
                            [
                              (self.authors[0], None),
                              (self.authors[1], None),
                              (self.authors[2], None),
                            ])
    self.assertEquals(result[0][1][1], 0)
    assertQueryResultsEqual(self, result[0][1][0],
                            [
                              (self.authors[1], self.authors[0].pk),
                              (self.authors[2], self.authors[0].pk),
                              (self.authors[0], self.authors[1].pk),
                              (self.authors[2], self.authors[1].pk),
                              (self.authors[0], self.authors[2].pk),
                              (self.authors[1], self.authors[2].pk),
                            ])
    self.assertEquals(result[1], Author)

  def test_recursive_m2m_to_self_avoids_loops(self):
    qs = 'Blog(%s) Blog.entry_set Entry.authors, Author.friends*' % self.blogs[0].pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0],
                            [
                              (self.authors[0], None),
                              (self.authors[1], None),
                              (self.authors[2], None),
                            ])
    self.assertEquals(result[0][1][1], 0)
    assertQueryResultsEqual(self, result[0][1][0],
                            [
                              (self.authors[1], self.authors[0].pk),
                              (self.authors[2], self.authors[0].pk),
                              (self.authors[0], self.authors[0].pk),
                              (self.authors[0], self.authors[1].pk),
                              (self.authors[1], self.authors[1].pk),
                              (self.authors[2], self.authors[1].pk),
                              (self.authors[0], self.authors[2].pk),
                              (self.authors[2], self.authors[2].pk),
                              (self.authors[1], self.authors[2].pk),
                            ])
    self.assertEquals(result[1], Author)
