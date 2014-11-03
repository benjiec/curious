from django.test import TestCase
from curious import model_registry
from curious.query import Query
from curious_tests.models import Blog, Entry, Author
from curious_tests import assertQueryResultsEqual
import curious_tests.models

class TestQueryFilters(TestCase):

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
    for i, author in enumerate(self.authors):
      author.age = (i+2)*10
      author.save()

    for i, entry in enumerate(self.entries):
      entry.authors.add(self.authors[i])
      entry.authors.add(self.authors[(i+1)%len(self.authors)])

    # register model
    model_registry.register(curious_tests.models)
    model_registry.get_manager('Blog').allowed_relationships = ['authors']

  def tearDown(self):
    model_registry.clear()

  def test_implicit_filter(self):
    qs = 'Blog(%s) Blog.authors(name__icontains="Smith")' % self.blogs[0].pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.authors[0], None)])
    self.assertEquals(result[1], Author)

  def test_explicit_filter(self):
    qs = 'Blog(%s) Blog.authors.filter(name__icontains="Smith")' % self.blogs[0].pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.authors[0], None)])
    self.assertEquals(result[1], Author)

  def test_explicit_exclude(self):
    qs = 'Blog(%s) Blog.authors.exclude(name__icontains="Smith")' % self.blogs[0].pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.authors[1], None),
                                                    (self.authors[2], None)])
    self.assertEquals(result[1], Author)

  def test_implicit_filter_followed_by_explicit_filter(self):
    qs = 'Blog(%s) Blog.authors(name__icontains="Jo").exclude(name__icontains="Smith")' % self.blogs[0].pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.authors[2], None)])
    self.assertEquals(result[1], Author)

  def test_explicit_chained_filters(self):
    qs = 'Blog(%s) Blog.authors.filter(name__icontains="Jo").exclude(name__icontains="Smith")' % self.blogs[0].pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.authors[2], None)])
    self.assertEquals(result[1], Author)

  def test_explicit_count_and_filter(self):
    qs = 'Blog(%s) Blog.entry_set.count(authors).filter(authors__count=2)' % self.blogs[0].pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.entries[0], None),
                                                    (self.entries[1], None),
                                                    (self.entries[2], None)])
    self.assertEquals(result[1], Entry)

    qs = 'Blog(%s) Blog.entry_set.count(authors).filter(authors__count=1)' % self.blogs[0].pk
    query = Query(qs)
    result = query()
    self.assertEquals(result, ([([], -1, None)], None))

  def test_explicit_avg_and_filter(self):
    qs = 'Blog(%s) Blog.entry_set.avg(authors__age).filter(authors__age__avg__gt=25)' % self.blogs[0].pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.entries[1], None),
                                                    (self.entries[2], None)])
    self.assertEquals(result[1], Entry)
