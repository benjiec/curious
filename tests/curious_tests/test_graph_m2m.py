from django.test import TestCase
from curious.graph import traverse
from curious_tests.models import Blog, Entry, Author
from curious_tests import assertQueryResultsEqual

class TestM2M(TestCase):

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

  def test_can_traverse_to_M2M_objects_and_returns_traversed_pair(self):
    authors = traverse(self.entries, Entry.authors)
    assertQueryResultsEqual(self, authors, [(self.authors[0], self.entries[0].pk),
                                            (self.authors[1], self.entries[0].pk),
                                            (self.authors[1], self.entries[1].pk),
                                            (self.authors[2], self.entries[1].pk),
                                            (self.authors[2], self.entries[2].pk),
                                            (self.authors[0], self.entries[2].pk)])

  def test_can_traverse_to_M2M_objects_with_filter(self):
    f = dict(method='filter', kwargs=dict(name__icontains='Smith'))
    authors = traverse(self.entries, Entry.authors, filters=[f])
    assertQueryResultsEqual(self, authors, [(self.authors[0], self.entries[0].pk),
                                            (self.authors[0], self.entries[2].pk)])

  def test_can_traverse_to_M2M_objects_with_exclusions(self):
    f = dict(method='exclude', kwargs=dict(name__icontains='Smith'))
    authors = traverse(self.entries, Entry.authors, filters=[f])
    assertQueryResultsEqual(self, authors, [(self.authors[1], self.entries[0].pk),
                                            (self.authors[1], self.entries[1].pk),
                                            (self.authors[2], self.entries[1].pk),
                                            (self.authors[2], self.entries[2].pk)])

  def test_can_traverse_from_M2M_objects_and_returns_traversed_pair(self):
    entries = traverse(self.authors, Author.entry_set)
    assertQueryResultsEqual(self, entries, [(self.entries[0], self.authors[0].pk),
                                            (self.entries[0], self.authors[1].pk),
                                            (self.entries[1], self.authors[1].pk),
                                            (self.entries[1], self.authors[2].pk),
                                            (self.entries[2], self.authors[2].pk),
                                            (self.entries[2], self.authors[0].pk)])

  def test_can_traverse_from_M2M_objects_with_filter(self):
    f = dict(method='filter', kwargs=dict(headline__icontains='Graph'))
    entries = traverse(self.authors, Author.entry_set, filters=[f])
    assertQueryResultsEqual(self, entries, [(self.entries[2], self.authors[2].pk),
                                            (self.entries[2], self.authors[0].pk)])

  def test_can_traverse_from_M2M_objects_with_exclusions(self):
    f = dict(method='exclude', kwargs=dict(headline__icontains='Graph'))
    entries = traverse(self.authors, Author.entry_set, filters=[f])
    assertQueryResultsEqual(self, entries, [(self.entries[0], self.authors[0].pk),
                                            (self.entries[0], self.authors[1].pk),
                                            (self.entries[1], self.authors[1].pk),
                                            (self.entries[1], self.authors[2].pk)])
