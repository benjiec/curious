import json
from django.test import TestCase
from curious import model_registry
from curious.query import Query
from curious_tests.models import Blog
from curious_tests import assertQueryResultsEqual


class MyModel(object):
  
  @staticmethod
  def fetch(ids):
    return [MyModel(i) for i in ids]

  def __init__(self, id):
    self.__id = id

  @property
  def pk(self):
    return 'my%s' % self.__id

  def fields(self):
    return ['a', 'b', 'c', 'id']

  def get(self, f):
    if f == 'id':
      return self.pk
    return '%s%s' % (f, self.__id)


@staticmethod
def blog_to_my_models_(instances, filter_f):
  r = [(MyModel(instance.pk), instance.pk) for instance in instances]
  return r


class TestCustomModel(TestCase):

  def setUp(self):
    blog = Blog(name='Databases')
    blog.save()
    self.blog = blog

    # add custom rel
    Blog.blog_to_my_models_ = blog_to_my_models_

    # register model
    model_registry.register(Blog)
    model_registry.register(MyModel)
    model_registry.get_manager('Blog').allowed_relationships = ['blog_to_my_models_']

  def tearDown(self):
    model_registry.clear()

  def test_query_starting_with_id(self):
    qs = 'Blog(%s)' % self.blog.pk
    query = Query(qs)
    result = query()
    self.assertEquals(len(result[0]), 1)
    self.assertEquals(result[0][0][1], -1)
    assertQueryResultsEqual(self, result[0][0][0], [(self.blog, None)])
    self.assertEquals(result[1], Blog)

  def test_traversing_to_custom_models(self):
    qs = 'Blog(%s) Blog.blog_to_my_models_' % self.blog.pk
    query = Query(qs)
    result = query()

    # last model
    self.assertEquals(result[1], MyModel)
    # one column
    self.assertEquals(len(result[0]), 1)

    # first column, no joins
    self.assertEquals(result[0][0][1], -1)
    # first column, one model object
    self.assertEquals(len(result[0][0][0]), 1)

    # type is right
    self.assertEquals(type(result[0][0][0][0][0]), MyModel)
    # id is right
    self.assertEquals(result[0][0][0][0][0].pk, 'my%s' % self.blog.pk)
    # no joins
    self.assertEquals(result[0][0][0][0][1], None)

  def test_fetch_custom_model_instances(self):
    data = dict(ids=[1,2,3])
    r = self.client.post('/curious/models/MyModel/', data=json.dumps(data), content_type='application/json')
    self.assertEquals(r.status_code, 200)
    results = json.loads(r.content)['result']
    print results
    self.assertEquals(results['fields'], ["a", "b", "c", "id"])
    self.assertItemsEqual(results['urls'], [None, None, None])
    self.assertItemsEqual(results['objects'],
                          [['a1', 'b1', 'c1', 'my1'],
                           ['a2', 'b2', 'c2', 'my2'],
                           ['a3', 'b3', 'c3', 'my3']])

