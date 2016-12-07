from django.test import TestCase
from curious import model_registry
from curious.query import Query
from curious_tests.models import Blog, Entry, Author
from curious_tests import assertQueryResultsEqual
import curious_tests.models

class TestQueryRecursive(TestCase):

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
    
    qs = 'Blog(%s) Blog.entry_set(headline__icontains="MySQL")' % self.blog.pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.entries[0], None)])
    self.assertEquals(result[1], Entry)

  def tearDown(self):
    model_registry.clear()

  def test_cannot_recursive_search_using_relationship_to_different_model(self):
    qs = 'Blog(%s) Blog.entry_set*' % self.blog.pk
    query = Query(qs)
    self.assertRaises(Exception, query)

  def test_recursive_search_with_no_criteria(self):
    qs = 'Blog(%s) Blog.entry_set(headline__icontains="MySQL") Entry.responses*' % self.blog.pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0],
                            [(self.entries[0], None),
                             (self.entries[1], None),
                             (self.entries[2], None),
                             (self.entries[3], None),
                            ])
    self.assertEquals(result[1], Entry)

  def test_recursive_search_with_filter_finds_starting_node(self):
    qs = 'Blog(%s) Blog.entry_set(headline__icontains="MySQL") \
          Entry.responses(headline__icontains="MySQL")*' % self.blog.pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.entries[0], None)])
    self.assertEquals(result[1], Entry)

  def test_recursive_search_with_filter_stops_traversal_after_mismatch(self):
    qs = 'Blog(%s) Blog.entry_set(headline__icontains="MySQL") \
          Entry.responses(headline__icontains="relational")*' % self.blog.pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0],
                            [(self.entries[0], None),
                             (self.entries[1], None)])
    self.assertEquals(result[1], Entry)

  def test_recursive_search_with_filter_does_not_return_starting_node_if_it_does_not_pass_filter(self):
    qs = 'Blog(%s) Blog.entry_set(headline__icontains="MySQL") \
          Entry.responses(headline__icontains="graph")*' % self.blog.pk
    query = Query(qs)
    result = query()
    self.assertEquals(result, ([([], -1, [])], None))

  def test_recursive_search_with_filter_does_not_contine_from_starting_node_if_it_does_not_pass_filter(self):
    qs = 'Blog(%s) Blog.entry_set(headline__icontains="MySQL") \
          Entry.responses(headline__icontains="Postgres")*' % self.blog.pk
    query = Query(qs)
    result = query()
    self.assertEquals(result, ([([], -1, [])], None))

  def test_recursive_traversal(self):
    qs = 'Blog(%s) Blog.entry_set(headline__icontains="MySQL") Entry.responses**' % self.blog.pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0],
                            [(self.entries[0], None),
                             (self.entries[1], None),
                             (self.entries[2], None),
                             (self.entries[3], None),
                            ])
    self.assertEquals(result[1], Entry)

  def test_recursive_traversal_with_filter_finds_starting_node(self):
    qs = 'Blog(%s) Blog.entry_set(headline__icontains="MySQL") \
          Entry.responses(headline__icontains="MySQL")**' % self.blog.pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.entries[0], None)])
    self.assertEquals(result[1], Entry)

  def test_recursive_traversal_with_filter_continues_traversal_after_mismatch(self):
    qs = 'Blog(%s) Blog.entry_set(headline__icontains="MySQL") \
          Entry.responses(headline__icontains="relational")**' % self.blog.pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0],
                            [(self.entries[0], None),
                             (self.entries[1], None),
                             (self.entries[3], None), # [2] did not match
                            ])
    self.assertEquals(result[1], Entry)

  def test_recursive_traversal_with_filter_does_not_return_starting_node_if_it_does_not_pass_filter(self):
    qs = 'Blog(%s) Blog.entry_set(headline__icontains="MySQL") \
          Entry.responses(headline__icontains="graph")**' % self.blog.pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0],
                            [(self.entries[2], None),
                             (self.entries[3], None),
                            ])
    self.assertEquals(result[1], Entry)

  def test_recursive_search_for_last_nodes_of_relationship(self):
    qs = 'Blog(%s) Blog.entry_set(headline__icontains="MySQL") Entry.responses$' % self.blog.pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.entries[3], None)])
    self.assertEquals(result[1], Entry)

  def test_recursive_search_for_last_node_passing_filter(self):
    qs = 'Blog(%s) Blog.entry_set(headline__icontains="MySQL") \
          Entry.responses(headline__icontains="relational")$' % self.blog.pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.entries[1], None)])
    self.assertEquals(result[1], Entry)
  
  def test_recursive_search_for_last_node_passing_filter_returns_starting_node(self):
    qs = 'Blog(%s) Blog.entry_set(headline__icontains="MySQL") \
          Entry.responses(headline__icontains="MySQL")$' % self.blog.pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.entries[0], None)])
    self.assertEquals(result[1], Entry)
  
  def test_recursive_search_for_first_node_matching_filter(self):
    qs = 'Blog(%s) Blog.entry_set(headline__icontains="MySQL") \
          Entry.responses(headline__icontains="graph")?' % self.blog.pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.entries[2], None)])
    self.assertEquals(result[1], Entry)

  def test_recursive_search_for_first_node_matching_filter_returns_starting_node(self):
    qs = 'Blog(%s) Blog.entry_set(headline__icontains="MySQL") \
          Entry.responses(headline__icontains="MySQL")?' % self.blog.pk
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.entries[0], None)])
    self.assertEquals(result[1], Entry)

  def test_recursive_traversal_from_same_model(self):
    qs = 'Entry(%s) Entry.responses*' % self.entries[0].id
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0],
                            [(self.entries[0], None),
                             (self.entries[1], None),
                             (self.entries[2], None),
                             (self.entries[3], None),
                            ])
    self.assertEquals(result[1], Entry)

  def test_recursive_traversal_from_same_model(self):
    qs = 'Entry(%s) Entry.responses*' % self.entries[0].id
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0],
                            [(self.entries[0], None),
                             (self.entries[1], None),
                             (self.entries[2], None),
                             (self.entries[3], None),
                            ])
    self.assertEquals(result[1], Entry)

  def test_recursive_traversal_on_same_model_from_multiple_objects(self):
    blog = Blog(name='Weird CS Terms')
    blog.save()
    headlines = ('Foo', 'Bar', 'Baz', 'Faz')
    entries = [Entry(headline=headline, blog=blog) for headline in headlines]
    for entry in entries:
      entry.save()
    entries[1].response_to = entries[0]
    entries[1].save()
    entries[2].response_to = entries[1]
    entries[2].save()
    entries[3].response_to = entries[2]
    entries[3].save()

    qs = 'Entry(id__in=[%s,%s]) Entry.responses*' % (self.entries[0].id, entries[0].id)
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0],
                            [(self.entries[0], None),
                             (self.entries[1], None),
                             (self.entries[2], None),
                             (self.entries[3], None),
                             (entries[0], None),
                             (entries[1], None),
                             (entries[2], None),
                             (entries[3], None),
                            ])
    self.assertEquals(result[1], Entry)

  def test_match_source_object_with_recursively_found_objects_including_self(self):
    qs = 'Entry(id__in=[%s]), Entry.responses*' % (self.entries[0].id,)
    query = Query(qs)
    result = query()

    self.assertEquals(len(result[0]), 2)
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.entries[0], None)])
    self.assertEquals(result[0][1][1], 0)
    assertQueryResultsEqual(self, result[0][1][0],
                            [(self.entries[0], self.entries[0].pk),
                             (self.entries[1], self.entries[0].pk),
                             (self.entries[2], self.entries[0].pk),
                             (self.entries[3], self.entries[0].pk)])
    self.assertEquals(result[1], Entry)

  def test_match_related_source_objects_with_recursively_found_objects(self):
    qs = 'Entry(id__in=[%s,%s]), Entry.responses*' % (self.entries[0].id, self.entries[1].id)
    query = Query(qs)
    result = query()

    self.assertEquals(len(result[0]), 2)
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.entries[0], None), (self.entries[1],None)])
    self.assertEquals(result[0][1][1], 0)
    assertQueryResultsEqual(self, result[0][1][0],
                            [(self.entries[0], self.entries[0].pk),
                             (self.entries[1], self.entries[0].pk),
                             (self.entries[2], self.entries[0].pk),
                             (self.entries[3], self.entries[0].pk),
                             (self.entries[1], self.entries[1].pk),
                             (self.entries[2], self.entries[1].pk),
                             (self.entries[3], self.entries[1].pk),
                            ])
    self.assertEquals(result[1], Entry)

  def test_recursive_traversal_does_not_get_stuck_in_loop(self):
    blog = Blog(name='Weird CS Terms')
    blog.save()
    headlines = ('Foo', 'Bar', 'Baz', 'Faz')
    entries = [Entry(headline=headline, blog=blog) for headline in headlines]
    for entry in entries:
      entry.save()
    entries[1].response_to = entries[0]
    entries[1].save()
    entries[2].response_to = entries[1]
    entries[2].save()
    entries[3].response_to = entries[2]
    entries[3].save()
    entries[0].response_to = entries[3]
    entries[0].save()

    qs = 'Entry(id__in=[%s]) Entry.responses*' % (entries[0].id,)
    query = Query(qs)
    result = query()
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0],
                            [(entries[0], None),
                             (entries[1], None),
                             (entries[2], None),
                             (entries[3], None),
                            ])
    self.assertEquals(result[1], Entry)
