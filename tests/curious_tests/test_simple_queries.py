from django.test import TestCase
from curious import model_registry
from curious.query import Query
from curious_tests.models import Blog, Entry, Author
from curious_tests import assertQueryResultsEqual
import curious_tests.models

class TestSimpleQueries(TestCase):

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

    model_registry.register(curious_tests.models)
    model_registry.get_manager('Blog').allowed_relationships = ['authors']

  def tearDown(self):
    model_registry.clear()

  def test_query_starting_with_id(self):
    qs = 'Entry(%s)' % self.entries[0].pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.entries[0], None)])
    self.assertEquals(result[1], Entry)

  def test_query_starting_with_filter(self):
    qs = 'Entry(id=%s)' % self.entries[0].pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.entries[0], None)])
    self.assertEquals(result[1], Entry)

  def test_query_with_empty_array_filter(self):
    qs = 'Entry(id__in=[])'
    query = Query(qs)
    result = query()
    self.assertFalse(result[0][0][0])

  def test_query_with_spaces_only_array_filter(self):
    qs = 'Entry(id__in=[  ])'
    query = Query(qs)
    result = query()
    self.assertFalse(result[0][0][0])

  def test_query_exlcuding_empty_array_filter(self):
    qs = 'Entry.exclude(id__in=[])'
    query = Query(qs)
    result = query()
    self.assertEquals(3, len(result[0][0][0]))

  def test_query_traversing_to_fk_object(self):
    qs = 'Entry(%s) Entry.blog' % self.entries[0].pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.blogs[0], None)])
    self.assertEquals(result[1], Blog)
  
  def test_query_traversing_from_fk_objects(self):
    qs = 'Blog(%s) Blog.entry_set' % self.blogs[0].pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.entries[0], None),
                                                    (self.entries[1], None),
                                                    (self.entries[2], None)])
    self.assertEquals(result[1], Entry)

  def test_query_traversing_to_M2M_objects(self):
    qs = 'Blog(%s) Blog.entry_set Entry.authors' % self.blogs[0].pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.authors[0], None),
                                                    (self.authors[1], None),
                                                    (self.authors[2], None)])
    self.assertEquals(result[1], Author)

  def test_query_traversing_with_function_and_from_M2M_objects(self):
    qs = 'Blog(%s) Blog.authors Author.entry_set' % self.blogs[0].pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.entries[0], None),
                                                    (self.entries[1], None),
                                                    (self.entries[2], None)])
    self.assertEquals(result[1], Entry)

  def test_query_traversing_with_filters(self):
    qs = 'Blog(%s) Blog.authors(name__icontains="Smith") Author.entry_set' % self.blogs[0].pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.entries[0], None),
                                                    (self.entries[2], None)])
    self.assertEquals(result[1], Entry)

  def test_query_traversing_with_exclusions(self):
    qs = 'Blog(%s) Blog.authors.exclude(name__icontains="Smith") Author.entry_set' % self.blogs[0].pk
    query = Query(qs)
    result = query()
    # should return all entries, since at least one author in each entry does
    # not have "Smith"
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.entries[0], None),
                                                    (self.entries[1], None),
                                                    (self.entries[2], None)])
    self.assertEquals(result[1], Entry)

    qs = 'Blog(%s) Blog.authors.exclude(name__icontains="Jo") Author.entry_set' % self.blogs[0].pk
    query = Query(qs)
    result = query()
    # should omit last entry, since both authors for that entry has Jo in their names
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.entries[0], None),
                                                    (self.entries[1], None)])
    self.assertEquals(result[1], Entry)
