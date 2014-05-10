from django.test import TestCase
from django.db import connection
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
    for i, author in enumerate(self.authors):
      author.age = (i+2)*10
      author.save()

    for i, entry in enumerate(self.entries):
      entry.authors.add(self.authors[i])
      entry.authors.add(self.authors[(i+1)%len(self.authors)])

  def test_single_filter(self):
    f = dict(method='filter', kwargs=dict(name__icontains='Smith'))
    authors = traverse(self.entries, Entry.authors, filters=[f])
    assertQueryResultsEqual(self, authors, [(self.authors[0], self.entries[0].pk),
                                            (self.authors[0], self.entries[2].pk)])

  def test_double_filter(self):
    f1 = dict(method='filter', kwargs=dict(name__icontains='Smith'))
    f2 = dict(method='filter', kwargs=dict(name__icontains='Joe'))
    authors = traverse(self.entries, Entry.authors, filters=[f1, f2])
    assertQueryResultsEqual(self, authors, [])

  def test_exclude(self):
    f = dict(method='exclude', kwargs=dict(name__icontains='Smith'))
    authors = traverse(self.entries, Entry.authors, filters=[f])
    assertQueryResultsEqual(self, authors, [(self.authors[1], self.entries[1].pk),
                                            (self.authors[2], self.entries[1].pk),
                                            (self.authors[2], self.entries[2].pk),
                                            (self.authors[1], self.entries[0].pk)])

  def test_double_exclude(self):
    f1 = dict(method='exclude', kwargs=dict(name__icontains='Joe'))
    f2 = dict(method='exclude', kwargs=dict(name__icontains='Smith'))
    authors = traverse(self.entries, Entry.authors, filters=[f1, f2])
    assertQueryResultsEqual(self, authors, [(self.authors[1], self.entries[1].pk),
                                            (self.authors[1], self.entries[0].pk)])

  def test_filter_and_exclude(self):
    f1 = dict(method='filter', kwargs=dict(name__icontains='Jo'))
    f2 = dict(method='exclude', kwargs=dict(name__icontains='Smith'))
    authors = traverse(self.entries, Entry.authors, filters=[f1, f2])
    assertQueryResultsEqual(self, authors, [(self.authors[2], self.entries[1].pk),
                                            (self.authors[2], self.entries[2].pk)])

  def test_count_and_filter(self):
    f1 = dict(method='count', field='authors')
    f2 = dict(method='filter', kwargs=dict(authors__count=3))
    entries = traverse(self.blogs, Blog.entry_set, filters=[f1, f2])
    assertQueryResultsEqual(self, entries, [])

    f1 = dict(method='count', field='authors')
    f2 = dict(method='filter', kwargs=dict(authors__count=2))
    entries = traverse(self.blogs, Blog.entry_set, filters=[f1, f2])
    assertQueryResultsEqual(self, entries, [(self.entries[0], self.blogs[0].pk),
                                            (self.entries[1], self.blogs[0].pk),
                                            (self.entries[2], self.blogs[0].pk)])

  def test_avg_and_filter(self):
    f1 = dict(method='avg', field='authors__age')
    f2 = dict(method='filter', kwargs=dict(authors__age__avg__gt=25))
    entries = traverse(self.blogs, Blog.entry_set, filters=[f1, f2])
    assertQueryResultsEqual(self, entries, [(self.entries[1], self.blogs[0].pk),
                                            (self.entries[2], self.blogs[0].pk)])

  def test_min_and_filter(self):
    f1 = dict(method='min', field='authors__age')
    f2 = dict(method='filter', kwargs=dict(authors__age__min__gt=25))
    entries = traverse(self.blogs, Blog.entry_set, filters=[f1, f2])
    assertQueryResultsEqual(self, entries, [(self.entries[1], self.blogs[0].pk)])

  def test_max_and_filter(self):
    f1 = dict(method='max', field='authors__age')
    f2 = dict(method='filter', kwargs=dict(authors__age__max__lt=35))
    entries = traverse(self.blogs, Blog.entry_set, filters=[f1, f2])
    assertQueryResultsEqual(self, entries, [(self.entries[0], self.blogs[0].pk)])

  def test_sum_and_filter(self):
    f1 = dict(method='sum', field='authors__age')
    f2 = dict(method='filter', kwargs=dict(authors__age__sum__gt=51))
    entries = traverse(self.blogs, Blog.entry_set, filters=[f1, f2])
    assertQueryResultsEqual(self, entries, [(self.entries[1], self.blogs[0].pk),
                                    (self.entries[2], self.blogs[0].pk)])
