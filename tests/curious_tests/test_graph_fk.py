from django.test import TestCase
from curious.graph import traverse
from curious_tests.models import Blog, Entry

class TestFK(TestCase):

  def setUp(self):
    blog = Blog(name='Databases')
    blog.save()
    self.blogs = [blog]

    headlines = ('MySQL is a relational DB',
                 'Postgres is a really good relational DB',
                 'Neo4J is a graph DB')
    self.entries = [Entry(headline=headline, blog=blog) for headline in headlines]
    for entry in self.entries:
      entry.save()

    blog = Blog(name='Graph Databases')
    blog.save()
    self.blogs.append(blog)
    entry = Entry(headline='Graph databases store edges with data', blog=blog)
    entry.save()
    self.entries.append(entry)

  def test_can_traverse_to_fk_objects_and_returns_traversed_pair(self):
    blogs = traverse(self.entries, Entry.blog)
    self.assertItemsEqual(blogs, [(self.blogs[0], self.entries[0].pk),
                                  (self.blogs[0], self.entries[1].pk),
                                  (self.blogs[0], self.entries[2].pk),
                                  (self.blogs[1], self.entries[3].pk)])

  def test_can_traverse_to_fk_objects_with_filter(self):
    blogs = traverse(self.entries, Entry.blog, filters=dict(name__icontains='graph'))
    self.assertItemsEqual(blogs, [(self.blogs[1], self.entries[3].pk)])

  def test_can_traverse_to_fk_objects_with_exclusions(self):
    f = {'__exclude__': True, 'name__icontains': 'graph'}
    blogs = traverse(self.entries, Entry.blog, filters=f)
    self.assertItemsEqual(blogs, [(self.blogs[0], self.entries[0].pk),
                                  (self.blogs[0], self.entries[1].pk),
                                  (self.blogs[0], self.entries[2].pk)])

  def test_can_traverse_from_fk_objects_and_returns_traversed_pair(self):
    entries = traverse(self.blogs, Blog.entry_set)
    self.assertItemsEqual(entries, [(self.entries[0], self.blogs[0].pk),
                                    (self.entries[1], self.blogs[0].pk),
                                    (self.entries[2], self.blogs[0].pk),
                                    (self.entries[3], self.blogs[1].pk)])

  def test_can_traverse_from_fk_objects_with_filter(self):
    entries = traverse(self.blogs, Blog.entry_set, filters=dict(headline__icontains='graph'))
    self.assertItemsEqual(entries, [(self.entries[2], self.blogs[0].pk),
                                    (self.entries[3], self.blogs[1].pk)])

  def test_can_traverse_from_fk_objects_with_exclusions(self):
    f = {'__exclude__': True, 'headline__icontains': 'graph'}
    entries = traverse(self.blogs, Blog.entry_set, filters=f)
    self.assertItemsEqual(entries, [(self.entries[0], self.blogs[0].pk),
                                    (self.entries[1], self.blogs[0].pk)])
