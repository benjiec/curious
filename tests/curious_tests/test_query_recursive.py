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
    self.blog = blog

    authors = ('John Smith', 'Jane Doe', 'Joe Plummer', 'Jessical Jones')
    headlines = ('MySQL is a good relational DB',
                 'Postgres is a really good relational DB',
                 'Neo4J is a graph DB',
                 'But we are not evaluating against graph DBs')

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

    # register model
    if len(model_registry.model_names) == 0:
      model_registry.register(curious_tests.models)
    
    qs = 'Blog(%s) Blog.entry_set(headline__icontains="MySQL")' % self.blog.pk
    query = Query(qs)
    result = query()
    assertQueryResultsEqual(self, result[0][0], [(self.entries[0], None)])
    self.assertEquals(result[1], Entry)

  def test_recursive_traversal_gets_all_nodes_including_self(self):
    qs = 'Blog(%s) Blog.entry_set(headline__icontains="MySQL") Entry.responses*' % self.blog.pk
    query = Query(qs)
    result = query()
    print result[0][0]
    assertQueryResultsEqual(self, result[0][0],
                            [(self.entries[0], None),
                              (self.entries[1], None),
                              (self.entries[2], None),
                              (self.entries[3], None),
                            ])
    self.assertEquals(result[1], Entry)

  def test_recursive_search_for_terminal_without_filter_returns_terminal_nodes(self):
    qs = 'Blog(%s) Blog.entry_set(headline__icontains="MySQL") Entry.responses**' % self.blog.pk
    query = Query(qs)
    result = query()
    assertQueryResultsEqual(self, result[0][0], [(self.entries[3], None)])
    self.assertEquals(result[1], Entry)

  def test_recursive_search_for_terminal_with_filter_returns_first_non_matching_node(self):
    qs = 'Blog(%s) Blog.entry_set(headline__icontains="MySQL") \
          Entry.responses(headline__icontains="relational")**' % self.blog.pk
    query = Query(qs)
    result = query()
    assertQueryResultsEqual(self, result[0][0], [(self.entries[2], None)])
    self.assertEquals(result[1], Entry)

  def test_cannot_recursive_search_using_relationship_to_different_model(self):
    qs = 'Blog(%s) Blog.entry_set*' % self.blog.pk
    query = Query(qs)
    self.assertRaises(Exception, query)
