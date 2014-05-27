from django.test import TestCase
from curious.query import Parser

class TestParser(TestCase):

  def test_parsing_relationship_and_filters(self):
    qs = 'Blog(1) Blog.entry_set Entry.authors(name__icontains="Smith")'
    q = Parser(qs)

    self.assertEquals(q.object_query['model'], 'Blog')
    self.assertEquals(q.object_query['method'], None)
    self.assertEquals(q.object_query['filters'], [dict(method='filter', kwargs=dict(id='1'))])
    self.assertEquals(q.steps,
      [dict(model='Blog', method='entry_set', filters=[]),
       dict(model='Entry', method='authors', filters=[dict(method='filter', kwargs=dict(name__icontains='Smith'))])])

  def test_parsing_multiple_filters(self):
    qs = 'Entry(1) Entry.authors(name__icontains="Smith").exclude(name__icontains="Joe")'
    q = Parser(qs)

    self.assertEquals(q.object_query['model'], 'Entry')
    self.assertEquals(q.object_query['method'], None)
    self.assertEquals(q.object_query['filters'], [dict(method='filter', kwargs=dict(id='1'))])
    self.assertEquals(q.steps,
      [dict(model='Entry', method='authors',
            filters=[
              dict(method='filter', kwargs=dict(name__icontains='Smith')),
              dict(method='exclude', kwargs=dict(name__icontains='Joe'))
            ])])

  def test_parsing_joins(self):
    qs = 'Blog(1), Blog.entry_set'
    q = Parser(qs)

    self.assertEquals(q.object_query['model'], 'Blog')
    self.assertEquals(q.object_query['method'], None)
    self.assertEquals(q.object_query['filters'], [dict(method='filter', kwargs=dict(id='1'))])
    self.assertEquals(q.steps, [dict(join=True, model='Blog', method='entry_set', filters=[])])

  def test_parsing_or_queries(self):
    qs = 'Blog(1), (Blog.entry_set_a) | (Blog.entry_set_b)'
    q = Parser(qs)

    self.assertEquals(q.object_query['model'], 'Blog')
    self.assertEquals(q.object_query['method'], None)
    self.assertEquals(q.object_query['filters'], [dict(method='filter', kwargs=dict(id='1'))])

    self.assertEquals(q.steps, [dict(join=True, orquery=[
                                 [dict(model='Blog', method='entry_set_a', filters=[])],
                                 [dict(model='Blog', method='entry_set_b', filters=[])]
                                ])])

  def test_parsing_sub_queries(self):
    qs = 'Blog(1) (Blog.entry_set)'
    q = Parser(qs)

    self.assertEquals(q.object_query['model'], 'Blog')
    self.assertEquals(q.object_query['method'], None)
    self.assertEquals(q.object_query['filters'], [dict(method='filter', kwargs=dict(id='1'))])
    self.assertEquals(q.steps, [dict(having=None, join=False, subquery=[
                                 dict(model='Blog', method='entry_set', filters=[]) ])])

  def test_parsing_sub_queries_with_plus(self):
    qs = 'Blog(1) +(Blog.entry_set)'
    q = Parser(qs)

    self.assertEquals(q.object_query['model'], 'Blog')
    self.assertEquals(q.object_query['method'], None)
    self.assertEquals(q.object_query['filters'], [dict(method='filter', kwargs=dict(id='1'))])
    self.assertEquals(q.steps, [dict(having='+', join=False, subquery=[
                                 dict(model='Blog', method='entry_set', filters=[]) ])])

  def test_parsing_sub_queries_with_minus(self):
    qs = 'Blog(1) -(Blog.entry_set)'
    q = Parser(qs)

    self.assertEquals(q.object_query['model'], 'Blog')
    self.assertEquals(q.object_query['method'], None)
    self.assertEquals(q.object_query['filters'], [dict(method='filter', kwargs=dict(id='1'))])
    self.assertEquals(q.steps, [dict(having='-', join=False, subquery=[
                                 dict(model='Blog', method='entry_set', filters=[]) ])])

  def test_parsing_left_join_sub_queries(self):
    qs = 'Blog(1) ?(Blog.entry_set)'
    q = Parser(qs)

    self.assertEquals(q.object_query['model'], 'Blog')
    self.assertEquals(q.object_query['method'], None)
    self.assertEquals(q.object_query['filters'], [dict(method='filter', kwargs=dict(id='1'))])
    self.assertEquals(q.steps, [dict(having='?', join=False, subquery=[
                                 dict(model='Blog', method='entry_set', filters=[]) ])])

  def test_parsing_or_query_in_sub_query(self):
    qs = 'Blog(1) ((Blog.entry_set_a)|(Blog.entry_set_b))'
    q = Parser(qs)

    self.assertEquals(q.object_query['model'], 'Blog')
    self.assertEquals(q.object_query['method'], None)
    self.assertEquals(q.object_query['filters'], [dict(method='filter', kwargs=dict(id='1'))])

    self.assertEquals(q.steps, [dict(having=None, join=False, subquery=[
                                 dict(join=False, orquery=[
                                   [dict(model='Blog', method='entry_set_a', filters=[])],
                                   [dict(model='Blog', method='entry_set_b', filters=[])]
                                 ])
                                ])])
