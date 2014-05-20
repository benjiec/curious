from django.test import TestCase
from curious import model_registry
from curious.query import Query
from curious_tests.models import Blog, Entry, Author
from curious_tests import assertQueryResultsEqual
import curious_tests.models

class TestQueryJoins(TestCase):

  def setUp(self):
    names = ('Databases', 'Relational Databases', 'Graph Databases')
    authors = ('John Smith', 'Jane Doe', 'Joe Plummer')
    headlines = ('MySQL is a relational DB',
                 'Postgres is a really good relational DB',
                 'Neo4J is a graph DB')

    self.blogs = [Blog(name=name) for name in names]
    for blog in self.blogs:
      blog.save()

    self.entries = [Entry(headline=headline, blog=blog) for headline, blog in zip(headlines, self.blogs)]
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

  def test_first_set_of_results_are_unique_and_not_separated_by_objects_from_first_relation(self):
    qs = 'Blog(name__icontains="Databases") Blog.entry_set Entry.authors'
    query = Query(qs)
    result = query()
    assertQueryResultsEqual(self, result[0][0], [(self.authors[0], None),
                                                 (self.authors[1], None),
                                                 (self.authors[2], None)])
    self.assertEquals(len(result[0]), 1)
    self.assertEquals(result[1], Author)

  def test_separates_second_set_of_results_by_objects_from_first_set_of_results(self):
    qs = 'Blog(name__icontains="Databases"), Blog.entry_set Entry.authors'
    query = Query(qs)
    result = query()
    assertQueryResultsEqual(self, result[0][0], [(self.blogs[0], None),
                                                 (self.blogs[1], None),
                                                 (self.blogs[2], None)])
    assertQueryResultsEqual(self, result[0][1], [(self.authors[0], self.blogs[0].pk),
                                                 (self.authors[1], self.blogs[0].pk),
                                                 (self.authors[1], self.blogs[1].pk),
                                                 (self.authors[2], self.blogs[1].pk),
                                                 (self.authors[2], self.blogs[2].pk),
                                                 (self.authors[0], self.blogs[2].pk)])
    self.assertEquals(len(result[0]), 2)
    self.assertEquals(result[1], Author)

  def test_outputs_of_filter_query_are_separated_by_inputs_to_filter_query(self):
    qs = 'Blog(name__icontains="Databases") (Blog.entry_set Entry.authors)'
    query = Query(qs)
    result = query()
    assertQueryResultsEqual(self, result[0][0], [(self.blogs[0], None),
                                                 (self.blogs[1], None),
                                                 (self.blogs[2], None)])
    assertQueryResultsEqual(self, result[0][1], [(self.authors[0], self.blogs[0].pk),
                                                 (self.authors[1], self.blogs[0].pk),
                                                 (self.authors[1], self.blogs[1].pk),
                                                 (self.authors[2], self.blogs[1].pk),
                                                 (self.authors[2], self.blogs[2].pk),
                                                 (self.authors[0], self.blogs[2].pk)])
    self.assertEquals(len(result[0]), 2)
    self.assertEquals(result[1], Blog)
