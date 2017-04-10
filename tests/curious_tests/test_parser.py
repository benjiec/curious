from django.test import TestCase
from curious.query import Parser
import humanize


class TestParserCore(TestCase):

  def test_parsing_model_and_filter(self):
    p = Parser('A(1)')
    self.assertEquals(p.object_query, {'model': 'A', 'method': None,
                                       'filters': [{'method': 'filter', 'kwargs': {'id': '1'}}]})
    self.assertEquals(p.steps, [])

  def test_parsing_kv_filters_in_steps(self):
    p = Parser('A(1) B.b(a=1, b="2", c=True, d=[1,2, 3])')
    self.assertEquals(p.object_query, {'model': 'A', 'method': None,
                                       'filters': [{'method': 'filter', 'kwargs': {'id': '1'}}]})
    self.assertEquals(p.steps, [{
      'model': 'B', 'method': 'b',
      'filters': [{'method': 'filter', 'kwargs': {'a': 1, 'b': '2', 'c': True, 'd': [1, 2, 3]}}]
    }])

  def test_parsing_relationship_and_filters(self):
    qs = 'Blog(1) Blog.entry_set Entry.authors(name__icontains="Smith")'
    q = Parser(qs)

    self.assertEquals(q.object_query['model'], 'Blog')
    self.assertEquals(q.object_query['method'], None)
    self.assertEquals(q.object_query['filters'], [dict(method='filter', kwargs=dict(id='1'))])
    self.assertEquals(q.steps, [
      dict(model='Blog', method='entry_set', filters=[]),
      dict(model='Entry', method='authors', filters=[
        dict(method='filter', kwargs=dict(name__icontains='Smith')),
      ])
    ])

  def test_parsing_multiple_filters(self):
    qs = 'Entry(1) Entry.authors(name__icontains="Smith").exclude(name__icontains="Joe")'
    q = Parser(qs)

    self.assertEquals(q.object_query['model'], 'Entry')
    self.assertEquals(q.object_query['method'], None)
    self.assertEquals(q.object_query['filters'], [dict(method='filter', kwargs=dict(id='1'))])
    self.assertEquals(q.steps, [dict(model='Entry', method='authors', filters=[
      dict(method='filter', kwargs=dict(name__icontains='Smith')),
      dict(method='exclude', kwargs=dict(name__icontains='Joe')),
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
      [dict(model='Blog', method='entry_set_b', filters=[])],
    ])])

  def test_parsing_sub_queries(self):
    qs = 'Blog(1) (Blog.entry_set)'
    q = Parser(qs)

    self.assertEquals(q.object_query['model'], 'Blog')
    self.assertEquals(q.object_query['method'], None)
    self.assertEquals(q.object_query['filters'], [dict(method='filter', kwargs=dict(id='1'))])
    self.assertEquals(q.steps, [dict(having=None, join=False, subquery=[
      dict(model='Blog', method='entry_set', filters=[]),
    ])])

  def test_parsing_sub_queries_with_plus(self):
    qs = 'Blog(1) +(Blog.entry_set)'
    q = Parser(qs)

    self.assertEquals(q.object_query['model'], 'Blog')
    self.assertEquals(q.object_query['method'], None)
    self.assertEquals(q.object_query['filters'], [dict(method='filter', kwargs=dict(id='1'))])
    self.assertEquals(q.steps, [dict(having='+', join=False, subquery=[
      dict(model='Blog', method='entry_set', filters=[]),
    ])])

  def test_parsing_sub_queries_with_minus(self):
    qs = 'Blog(1) -(Blog.entry_set)'
    q = Parser(qs)

    self.assertEquals(q.object_query['model'], 'Blog')
    self.assertEquals(q.object_query['method'], None)
    self.assertEquals(q.object_query['filters'], [dict(method='filter', kwargs=dict(id='1'))])
    self.assertEquals(q.steps, [dict(having='-', join=False, subquery=[
      dict(model='Blog', method='entry_set', filters=[]),
    ])])

  def test_parsing_left_join_sub_queries(self):
    qs = 'Blog(1) ?(Blog.entry_set)'
    q = Parser(qs)

    self.assertEquals(q.object_query['model'], 'Blog')
    self.assertEquals(q.object_query['method'], None)
    self.assertEquals(q.object_query['filters'], [dict(method='filter', kwargs=dict(id='1'))])
    self.assertEquals(q.steps, [dict(having='?', join=False, subquery=[
      dict(model='Blog', method='entry_set', filters=[])
    ])])

  def test_parsing_or_query_in_sub_query(self):
    qs = 'Blog(1) ((Blog.entry_set_a)|(Blog.entry_set_b))'
    q = Parser(qs)

    self.assertEquals(q.object_query['model'], 'Blog')
    self.assertEquals(q.object_query['method'], None)
    self.assertEquals(q.object_query['filters'], [dict(method='filter', kwargs=dict(id='1'))])

    self.assertEquals(q.steps, [
      dict(having=None, join=False, subquery=[
        dict(join=False, orquery=[
          [dict(model='Blog', method='entry_set_a', filters=[])],
          [dict(model='Blog', method='entry_set_b', filters=[])],
        ]),
      ])
    ])


class TestDateTimeParsing(TestCase):

  def test_does_not_auto_convert_date_strings(self):
    p = Parser('A(1) B.b(a="3 days ago")')
    self.assertEquals(p.steps, [{'model': 'B', 'method': 'b',
                                 'filters': [{'method': 'filter',
                                              'kwargs': {'a': '3 days ago'}}]}])

  def test_converts_date_strings_with_years(self):
    p = Parser('A(1) B.b(a=t"3 years ago")')
    t = p.steps[0]['filters'][0]['kwargs']['a']
    t_natural = str(humanize.naturaltime(t))
    self.assertEquals(t_natural, "3 years ago")

    p = Parser('A(1) B.b(a=t"10 years from now")')
    t = p.steps[0]['filters'][0]['kwargs']['a']
    t_natural = str(humanize.naturaltime(t))
    self.assertEquals(t_natural, "10 years from now")

  def test_converts_date_strings_with_days(self):
    p = Parser('A(1) B.b(a=t"3 days ago")')
    t = p.steps[0]['filters'][0]['kwargs']['a']
    t_natural = str(humanize.naturaltime(t))
    self.assertEquals(t_natural, "3 days ago")

    p = Parser('A(1) B.b(a=t"3 days 15 minutes from now")')
    t = p.steps[0]['filters'][0]['kwargs']['a']
    t_natural = str(humanize.naturaltime(t))
    self.assertEquals(t_natural, "3 days from now")

  def test_converts_date_strings_with_minutes(self):
    p = Parser('A(1) B.b(a=t"2 minutes ago")')
    t = p.steps[0]['filters'][0]['kwargs']['a']
    t_natural = str(humanize.naturaltime(t))
    self.assertEquals(t_natural, "2 minutes ago")

    p = Parser('A(1) B.b(a=t"10 minutes 10 seconds from now")')
    t = p.steps[0]['filters'][0]['kwargs']['a']
    t_natural = str(humanize.naturaltime(t))
    self.assertEquals(t_natural, "10 minutes from now")

  def test_converts_date_strings_with_seconds(self):
    p = Parser('A(1) B.b(a=t"10 seconds ago")')
    t = p.steps[0]['filters'][0]['kwargs']['a']
    t_natural = str(humanize.naturaltime(t))
    self.assertEquals(t_natural, "10 seconds ago")

    p = Parser('A(1) B.b(a=t"10 seconds from now")')
    t = p.steps[0]['filters'][0]['kwargs']['a']
    t_natural = str(humanize.naturaltime(t))
    self.assertIn(t_natural, ["10 seconds from now", "9 seconds from now"])

  def test_converts_date_strings_with_year_and_days_incorrectly(self):
    p = Parser('A(1) B.b(a=t"1 year 3 days ago")')
    t = p.steps[0]['filters'][0]['kwargs']['a']
    t_natural = str(humanize.naturaltime(t))
    self.assertIn("11 months", t_natural)

  def test_converts_a_specific_date(self):
    p = Parser('A(1) B.b(a=t"Aug 22nd 2014")')
    t = p.steps[0]['filters'][0]['kwargs']['a']
    self.assertEquals(t.year, 2014)
    self.assertEquals(t.month, 8)
    self.assertEquals(t.day, 22)

    p = Parser('A(1) B.b(a=t"8/22/2014")')
    t = p.steps[0]['filters'][0]['kwargs']['a']
    self.assertEquals(t.year, 2014)
    self.assertEquals(t.month, 8)
    self.assertEquals(t.day, 22)
