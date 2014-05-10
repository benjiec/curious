from django.test import TestCase
from curious.graph import traverse
from curious_tests.models import Blog, Entry, Author
from curious_tests import assertQueryResultsEqual

class TestFunc(TestCase):

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

  def test_can_traverse_via_function_and_returns_traversed_pair(self):
    authors = traverse(self.blogs, Blog.authors)
    assertQueryResultsEqual(self, authors, Blog.authors(self.blogs))

  def test_can_traverse_via_function_with_filter(self):
    f = dict(method='filter', kwargs=dict(name__icontains='Smith'))
    authors = traverse(self.blogs, Blog.authors, filters=[f])
    assertQueryResultsEqual(self, authors, [x for x in Blog.authors(self.blogs) if 'Smith' in x[0].name])

  def test_can_traverse_via_function_with_exclusions(self):
    f = dict(method='exclude', kwargs=dict(name__icontains='Smith'))
    authors = traverse(self.blogs, Blog.authors, filters=[f])
    assertQueryResultsEqual(self, authors, [x for x in Blog.authors(self.blogs) if 'Smith' not in x[0].name])
