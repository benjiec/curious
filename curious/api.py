import json
import types
import time
from django.core.cache import cache
from django.db.models.fields.related import ReverseSingleRelatedObjectDescriptor
from django.db.models.fields.related import ForeignKey
from django.http import HttpResponse
from django.views.generic.base import View

from curious import model_registry
from .query import Query
from .utils import report_time


class JSONView(View):

  def _return(self, code, result):
    res = {'result': result}
    return HttpResponse(json.dumps(res), status=code, content_type='application/json')

  def _error(self, code, message):
    res = {'error': {'message': message}}
    return HttpResponse(json.dumps(res), status=code, content_type='application/json')


class ModelListView(JSONView):

  def get(self, request):
    return self._return(200, model_registry.model_names)


class ModelView(JSONView):

  @staticmethod
  def model_to_dict(cls):
    d = dict(model=cls.__name__, relationships=[])
    for f in dir(cls):
      if model_registry.is_rel_allowed(cls, f):
        d['relationships'].append(f)
    return d

  @staticmethod
  def objects_to_dict(objects):
    if len(objects) == 0:
      return dict(fields=[], objects=[])

    fields = []
    fk = []
    obj = objects[0]
    for f in obj._meta.fields:
      fields.append(f.column)
      fk.append(f.name if type(f) == ForeignKey else None)

    packed = []
    for obj in objects:
      values = []
      for column, fk_name in zip(fields, fk):
        value = getattr(obj, column)
        if not type(value) in (long, int, float, bool, types.NoneType):
          value = unicode(value)
        if fk_name is not None:
          v = getattr(obj, fk_name)
          if v is not None:
            model_name = model_registry.getname(v.__class__)
            try:
              url = model_registry.geturl(model_name, v)
            except:
              url = None
            value = (model_name, v.pk, str(v), url)
        values.append(value)
      packed.append(values)

    return dict(fields=fields, objects=packed)

  def get(self, request, model_name):
    try:
      cls = model_registry.getclass(model_name)
    except Exception as e:
      return self._error(404, "Unknown model '%s': %s" % (model_name, str(e)))
    return self._return(200, ModelView.model_to_dict(cls))

  @report_time
  def post(self, request, model_name):
    """
    Fetch objects in batch.
    """

    try:
      data = json.loads(request.body)
    except:
      return self._error(400, "Bad data")

    if 'ids' not in data:
      return self._error(400, "Missing ids array")

    try:
      cls = model_registry.getclass(model_name)
    except:
      return self._error(404, "Unknown model '%s'" % model_name)

    t = time.time()
    r = cls.objects.filter(id__in=data['ids'])
    r = list(r)
    print 'fetch %.2f' % (time.time()-t,)
    t = time.time()
    r = ModelView.objects_to_dict(r)
    print ' pack %.2f' % (time.time()-t,)
    return self._return(200, r)


class ObjectView(JSONView):

  @staticmethod
  def object_to_dict(obj):
    d = {}
    for f in obj._meta.fields:
      d[f.column] = getattr(obj, f.column)
      if not type(d[f.column]) in (long, int, float, bool, types.NoneType):
        d[f.column] = unicode(d[f.column]);
      if type(f) == ForeignKey:
        v = getattr(obj, f.name)
        if v is not None:
          model_name = model_registry.getname(v.__class__)
          d[f.column] = {
            'model': model_name,
            'id': v.pk,
            '__str__': str(v)
          }
          try:
            d[f.column]['url'] = model_registry.geturl(model_name, v)
          except:
            pass
    return d

  def get(self, request, model_name, id):
    try:
      cls = model_registry.getclass(model_name)
    except:
      return self._error(404, "Unknown model '%s'" % model_name)
    try:
      obj = cls.objects.get(pk=id)
    except:
      return self._error(404, "Cannot find instance '%s' on '%s'" % (id, model_name))
    return self._return(200, ObjectView.object_to_dict(obj))


class QueryView(JSONView):

  def get_query_results(self, query, force):
    k = hash(query.query_string)
    v = cache.get(k)
    if v is None or force:
      v = self.run_query(query)
      cache.set(k, v, None)
    return v

  def run_query(self, query):
    res, last_model = query()
    results = []
    for obj_src in res:
      model = type(obj_src[0][0])
      if model._deferred:
        model = model.__base__
      model_name = model_registry.getname(model)
      d = {'model': model_name,
           'objects': [(obj.pk, model_registry.geturl(model_name, obj), src) for obj, src in obj_src]
          }
      results.append(d)
    if last_model is not None:
      return dict(last_model=model_registry.getname(last_model), results=results)
    else:
      return dict(last_model=None, results=results)

  @report_time
  def get(self, request):
    if 'q' not in request.GET:
      return self._error(400, 'Missing query')

    q = request.GET['q']

    try:
      query = Query(q)
    except Exception as e:
      import traceback
      traceback.print_exc()
      return self._error(400, str(e))

    # check query mode
    if 'c' in request.GET:
      return self._return(200, dict(query=q))

    try:
      results = self.get_query_results(query, 'r' in request.GET)
    except Exception as e:
      import traceback
      traceback.print_exc()
      return self._error(400, str(e))

    # print results
    return self._return(200, results)
