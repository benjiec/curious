import datetime
import humanize
from unittest import TestCase
from curious.parser import Parser

class ParserTests(TestCase):

  def test_parses_model_and_filter(self):
    p = Parser('A(1)')
    self.assertEquals(p.object_query, {'model': 'A', 'method': None,
                                       'filters': [{'method': 'filter', 'kwargs': {'id': '1'}}]})
    self.assertEquals(p.steps, [])

  def test_parses_kv_filters_in_steps(self):
    p = Parser('A(1) B.b(a=1, b="2", c=True, d=[1,2, 3])')
    self.assertEquals(p.object_query, {'model': 'A', 'method': None,
                                       'filters': [{'method': 'filter', 'kwargs': {'id': '1'}}]})
    self.assertEquals(p.steps, [{'model': 'B', 'method': 'b',
                                 'filters': [{'method': 'filter',
                                              'kwargs': {'a': 1,
                                                         'b': '2',
                                                         'c': True,
                                                         'd': [1,2,3]} }]}])

  def test_does_not_auto_convert_date_strings(self):
    p = Parser('A(1) B.b(a="3 days ago")')
    self.assertEquals(p.steps, [{'model': 'B', 'method': 'b',
                                 'filters': [{'method': 'filter',
                                              'kwargs': {'a': '3 days ago'} }]}])

  def test_converts_date_strings_with_years(self):
    p = Parser('A(1) B.b(a=t"3 years ago")')
    t = p.steps[0]['filters'][0]['kwargs']['a']
    s = str(humanize.naturaltime(t))
    self.assertEquals(s, "3 years ago")

    p = Parser('A(1) B.b(a=t"3 years from now")')
    t = p.steps[0]['filters'][0]['kwargs']['a']
    s = str(humanize.naturaltime(t))
    self.assertEquals(s, "3 years from now")

  def test_converts_date_strings_with_days(self):
    p = Parser('A(1) B.b(a=t"3 days ago")')
    t = p.steps[0]['filters'][0]['kwargs']['a']
    s = str(humanize.naturaltime(t))
    self.assertEquals(s, "3 days ago")

    p = Parser('A(1) B.b(a=t"3 days 15 minutes from now")')
    t = p.steps[0]['filters'][0]['kwargs']['a']
    s = str(humanize.naturaltime(t))
    self.assertEquals(s, "3 days from now")

  def test_converts_date_strings_with_minutes(self):
    p = Parser('A(1) B.b(a=t"2 minutes ago")')
    t = p.steps[0]['filters'][0]['kwargs']['a']
    s = str(humanize.naturaltime(t))
    self.assertEquals(s, "2 minutes ago")

    p = Parser('A(1) B.b(a=t"10 minutes 10 seconds from now")')
    t = p.steps[0]['filters'][0]['kwargs']['a']
    s = str(humanize.naturaltime(t))
    self.assertEquals(s, "10 minutes from now")
    
  def test_converts_date_strings_with_seconds(self):
    p = Parser('A(1) B.b(a=t"10 seconds ago")')
    t = p.steps[0]['filters'][0]['kwargs']['a']
    s = str(humanize.naturaltime(t))
    self.assertEquals(s, "10 seconds ago")

    p = Parser('A(1) B.b(a=t"10 seconds from now")')
    t = p.steps[0]['filters'][0]['kwargs']['a']
    s = str(humanize.naturaltime(t))
    self.assertEquals(s in ["10 seconds from now", "9 seconds from now"], True)
    
  def test_converts_date_strings_with_year_and_days_incorrectly(self):
    p = Parser('A(1) B.b(a=t"1 year 3 days ago")')
    t = p.steps[0]['filters'][0]['kwargs']['a']
    s = str(humanize.naturaltime(t))
    self.assertEquals(s, "11 months ago")

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
