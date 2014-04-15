import json
import types
from django.db.models.fields.related import ReverseSingleRelatedObjectDescriptor
from django.http import HttpResponse
from django.views.generic.base import View

from curious import model_registry
from .graph import _valid_django_rel
from .query import Query


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
      if _valid_django_rel(getattr(cls, f)) or model_registry.allow_rel(cls.__name__, f):
        d['relationships'].append(f)
    return d

  def get(self, request, model_name):
    try:
      cls = model_registry.getclass(model_name)
    except:
      return self._error(404, "Unknown model '%s'" % model_name)
    return self._return(200, ModelView.model_to_dict(cls))


class ObjectView(JSONView):

  @staticmethod
  def object_to_dict(obj):
    d = {k: v for k, v in obj.__dict__.iteritems()
         if type(v) in (long, int, float, str, unicode, bool, types.NoneType)}

    # find foreign keys
    for f in dir(obj):
      k = '%s_id' % f
      if k in d and type(getattr(obj.__class__, f)) == ReverseSingleRelatedObjectDescriptor:
        v = getattr(obj, f)
        if v is not None:
          d[k] = {'model': v.__class__.__name__, 'id': v.pk, '__str__': str(v)}
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
      objects = query()
    except Exception as e:
      import traceback
      traceback.print_exc()
      return self._error(400, str(e))

    if len(objects) == 0:
      results = {}
      return self._return(200, results)

    models = list(set([type(obj).__name__ for obj in objects]))
    assert len(models) == 1

    results = {'model': models[0], 'ids': [obj.pk for obj in objects]}
    return self._return(200, results)
