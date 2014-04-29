import json
import types
from django.db.models.fields.related import ReverseSingleRelatedObjectDescriptor
from django.db.models.fields.related import ForeignKey
from django.http import HttpResponse
from django.views.generic.base import View

from curious import model_registry
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
      if model_registry.is_rel_allowed(cls, f):
        d['relationships'].append(f)
    return d

  def get(self, request, model_name):
    try:
      cls = model_registry.getclass(model_name)
    except Exception as e:
      return self._error(404, "Unknown model '%s': %s" % (model_name, str(e)))
    return self._return(200, ModelView.model_to_dict(cls))

  def post(self, request, model_name):
    """
    Fetch objects in batch.
    """

    if 'ids' not in request.POST:
      return self._error(400, "Missing ids array")

    try:
      cls = model_registry.getclass(model_name)
    except:
      return self._error(404, "Unknown model '%s'" % model_name)

    r = []
    for id in request.POST['ids']:
      try:
        obj = cls.objects.get(pk=id)
      except:
        r.append(ObjectView.object_to_dict(obj))

    return self._return(200, r)


class ObjectView(JSONView):

  @staticmethod
  def object_to_dict(obj):
    d = {}
    for f in obj._meta.fields:
      d[f.column] = unicode(getattr(obj, f.column))
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
      res = query()
    except Exception as e:
      import traceback
      traceback.print_exc()
      return self._error(400, str(e))

    results = []
    for obj_src in res:
      model = type(obj_src[0][0])
      model_name = model_registry.getname(model)

      d = {'model': model_name,
           'objects': [(obj.pk, model_registry.geturl(model_name, obj), src) for obj, src in obj_src]
          }
      results.append(d)

    # print results
    return self._return(200, results)
