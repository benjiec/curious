import json
import types
from decimal import Decimal
from datetime import datetime
from humanize import naturaltime
from django.core.cache import cache
from django.db.models.fields.related import ReverseSingleRelatedObjectDescriptor
from django.db.models.fields.related import ForeignKey
from django.http import HttpResponse
from django.views.generic.base import View

from curious import model_registry
from .query import Query
from .utils import report_time
import time


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
    model_name = model_registry.get_name(cls)
    d = dict(model=model_name, relationships=[])
    for f in dir(cls):
      if model_registry.get_manager(model_name).is_rel_allowed(f):
        d['relationships'].append(f)
    return d

  @staticmethod
  def objects_to_dict(objects, ignore_excludes=False, follow_fk=True):
    if len(objects) == 0:
      return dict(fields=[], objects=[])

    fields = []
    fk = []
    is_model = True
    add_pk = False

    obj = objects[0]
    model_name = model_registry.get_name(obj.__class__)
    if ignore_excludes is True:
      excludes = []
    else:
      excludes = model_registry.get_manager(model_name).field_excludes

    if hasattr(obj, '_meta'):
      for f in obj._meta.fields:
        if f.column not in excludes:
          fields.append(f.column)
          fk.append(f.name if type(f) == ForeignKey else None)
      if 'id' not in fields:
        fields.append('pk')
        fk.append(None)
        add_pk = True
    else:
      is_model = False
      for f in obj.fields():
        fields.append(f)
        fk.append(None)

    packed = []
    urls = []
    for obj in objects:
      obj_url = model_registry.get_manager(model_name).url_of(obj)
      values = []

      for column, fk_name in zip(fields, fk):
        if is_model:
          value = getattr(obj, column)
        else:
          value = obj.get(column)

        if type(value) is Decimal:
          value = float(value)
        elif not type(value) in (long, int, float, bool, types.NoneType):
          value = unicode(value)
        if fk_name is not None and follow_fk is True:
          v = getattr(obj, fk_name)
          if v is not None:
            fk_model_name = model_registry.get_name(v.__class__)
            fk_url = None
            try:
              fk_url = model_registry.get_manager(fk_model_name).url_of(v)
            except:
              fk_url = None
            value = (fk_model_name, v.pk, str(v), fk_url)
        values.append(value)

      urls.append(obj_url)
      packed.append(values)

    if add_pk is True:
      assert fields[-1] == 'pk'
      fields[-1] = 'id'
    return dict(fields=fields, objects=packed, urls=urls)

  def get(self, request, model_name):
    try:
      cls = model_registry.get_manager(model_name).model_class
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
      cls = model_registry.get_manager(model_name).model_class
    except:
      return self._error(404, "Unknown model '%s'" % model_name)

    if hasattr(cls, '_meta'):
      fks = []
      for f in cls._meta.fields:
        if type(f) == ForeignKey:
          fks.append(f.name)

      q = cls.objects.filter(pk__in=data['ids'])
      if len(fks) > 0:
        q = q.select_related(*fks)
      r = ModelView.objects_to_dict(list(q), 'x' in data)

    else:
      objs = cls.fetch(data['ids'])
      r = ModelView.objects_to_dict(objs, 'x' in data)

    return self._return(200, r)


class ObjectView(JSONView):

  @staticmethod
  def object_to_dict(obj):
    d = {}
    for f in obj._meta.fields:
      d[f.column] = getattr(obj, f.column)
      if not type(d[f.column]) in (long, int, float, bool, types.NoneType):
        d[f.column] = unicode(d[f.column])
      if type(f) == ForeignKey:
        v = getattr(obj, f.name)
        if v is not None:
          model_name = model_registry.get_name(v.__class__)
          d[f.column] = {
            'model': model_name,
            'id': v.pk,
            '__str__': str(v)
          }
          try:
            d[f.column]['url'] = model_registry.get_manager(model_name).url_of(v)
          except:
            pass
    if 'id' not in d:
      pk = obj.pk
      if not type(pk) in (long, int, float, bool, types.NoneType):
        d['id'] = unicode(pk)
      else:
        d['id'] = pk
    return d

  def get(self, request, model_name, id):
    try:
      cls = model_registry.get_manager(model_name).model_class
    except:
      return self._error(404, "Unknown model '%s'" % model_name)
    try:
      obj = cls.objects.get(pk=id)
    except:
      return self._error(404, "Cannot find instance '%s' on '%s'" % (id, model_name))
    return self._return(200, ObjectView.object_to_dict(obj))


class QueryView(JSONView):
  # if query takes longer than this number of seconds, cache it
  QUERY_TIME_CACHING_THRESHOLD = 10

  def get_query_results(self, query, force):
    k = hash('v%d_%s' % (4, query.query_string))
    v = cache.get(k)
    if v is None or force:
      t = time.time()
      v = self.run_query(query)
      t = time.time()-t
      if t > QueryView.QUERY_TIME_CACHING_THRESHOLD:
        cache.set(k, v, None)
      else:
        # remove old cache if there are any
        cache.set(k, None)
    return v

  def run_query(self, query):
    res, last_model = query()
    results = []

    for obj_src, join_index in res:
      model = None
      for obj, src in obj_src:
        if obj is not None:
          model = obj.__class__
          if hasattr(model, '_deferred') and model._deferred:
            model = model.__base__
          break

      if model is not None:
        model_name = model_registry.get_name(model)
      else:
        model_name = None

      d = {'model': model_name,
           'join_index': join_index,
           'objects': [(obj.pk, src) if obj is not None else (None, src) for obj, src in obj_src]
          }
      results.append(d)

    if last_model is not None:
      last_model = model_registry.get_name(last_model)

    return dict(last_model=last_model, results=results, computed_on=datetime.now())

  @report_time
  def _process(self, params):
    if 'q' not in params:
      return self._error(400, 'Missing query')

    q = params['q']
    print q

    try:
      query = Query(q)
    except Exception as e:
      import traceback
      traceback.print_exc()
      return self._error(400, str(e))

    # check query mode
    if 'c' in params:
      return self._return(200, dict(query=q))

    try:
      results = self.get_query_results(query, 'r' in params)
    except Exception as e:
      import traceback
      traceback.print_exc()
      return self._error(400, str(e))

    t = datetime.now()-results['computed_on']
    if t.seconds > 300:
      results['computed_since'] = str(naturaltime(results['computed_on']))
    results['computed_on'] = str(results['computed_on'])

    # data mode
    objects = []
    if 'd' in params:
      follow_fk = True
      if 'fk' in params and params['fk'] in ('0','false'):
        follow_fk = False
      t0 = datetime.now()
      for result in results['results']:
        if result['model']:
          model = model_registry.get_manager(result['model']).model_class
          ids = [t[0] for t in result['objects']]
          if hasattr(model, '_meta'):
            objs = model.objects.filter(pk__in=ids)
          else:
            objs = model.fetch(ids)
          objs = ModelView.objects_to_dict(objs, 'x' in params, follow_fk=follow_fk)
          objects.append(objs)
        else:
          objects.append([])
      results['data'] = objects
      t1 = datetime.now()
      print 'DATA IN %s' % (t1-t0,)

    # print results
    return self._return(200, results)

  def get(self, request):
    return self._process(request.GET)

  def post(self, request):
    return self._process(request.POST)
