import time
from curious import model_registry
from curious.graph import traverse, mk_filter_function
from .parser import Parser
from .utils import report_time


class Query(object):

  def __init__(self, query):
    parser = Parser(query)
    self.__query = query
    self.__obj_query = parser.object_query
    self.__steps = parser.steps
    self.__validate()


  @property
  def query_string(self):
    return self.__query


  @staticmethod
  def _validate(query):
    """
    Validate a query. A query is an array whose elements are model
    relationships or subqueries. This function checks each model relationship
    to make sure the model and the relationship exist.
    """
    
    for rel in query:
      if 'orquery' in rel:
        for q in rel['orquery']:
          Query._validate(q)
      elif 'subquery' in rel:
        Query._validate(rel['subquery'])
      else:
        model = rel['model']
        method = rel['method']
        if method is None:
          model_registry.get_manager(model).model_class
        else:
          model_registry.get_manager(model).getattr(method)


  def __validate(self):
    Query._validate([self.__obj_query]+self.__steps)


  def __get_objects(self):
    """
    Get initial objects from object query.
    """

    model = self.__obj_query['model']
    method = self.__obj_query['method']
    filters = self.__obj_query['filters']
    filter_f = mk_filter_function(filters)

    if method is None:
      cls = model_registry.get_manager(model).model_class
      q = cls.objects.all()
      q = filter_f(q)
      return q
    else:
      f = model_registry.get_manager(model).getattr(method)
      return f(filter_f)


  @staticmethod
  def _extend_result(obj_src, next_obj_src):
    # build input hash of IDs
    input_map = {}
    for obj, src in obj_src:
      if obj.pk not in input_map:
        input_map[obj.pk] = []
      input_map[obj.pk].append(src)

    keep = []
    for next_obj, next_src in next_obj_src:
      if next_src in input_map:
        for src in input_map[next_src]:
          keep.append((next_obj, src))

    return list(set(keep))


  @staticmethod
  @report_time
  def _graph_step(obj_src, model, step_f, filters, tree=None):
    """
    Traverse one step on the graph. Takes in and returns arrays of output,
    input object tuples. The input objects in the tuples are from start of the
    query, not start of this step.
    """

    # check if type matches existing object type
    if len(obj_src):
      t = type(obj_src[0][0])
      if hasattr(t, '_deferred') and t._deferred:
        t = t.__base__
      if t != model_registry.get_manager(model).model_class:
        raise Exception('Type mismatch when executing query: expecting "%s", got "%s"' %
                        (model, type(obj_src[0][0])))

    next_obj_src = traverse([obj for obj, src in obj_src], step_f, filters)
    if tree is not None:
      tree.extend((t[0].id, t[1]) for t in next_obj_src)

    return Query._extend_result(obj_src, next_obj_src)


  @staticmethod
  def _recursive_rel(obj_src, step):
    """
    Traverse a relationship recursively. Collected objects, either loop
    terminating objects or loop continuing objects. Returns arrays of output,
    input object tuples. The input objects in the tuples are from start of the
    query, not start of this step.
    """

    model = step['model']
    method = step['method']
    filters = step['filters']
    collect = step['collect']
    step_f = model_registry.get_manager(model).getattr(method)

    collected = {}
    tree = []
    starting = True

    if collect == 'search' and filters is None:
      return obj_src
    
    to_remove = []
    if collect in ("all", "until", "search"):
      # if traversal or search, then keep starting nodes if starting nodes pass filter
      if filters in (None, {}, []):
        for tup in obj_src:
          collected[tup] = 1
      else:
        filter_f = mk_filter_function(filters)
        if len(obj_src) > 0:
          ids = [obj.id for obj, src in obj_src]
          q = obj_src[0][0].__class__.objects.filter(id__in=ids)
          q = filter_f(q)
          matched_objs = {obj.pk: 1 for obj in q}
          for tup in obj_src:
            if tup[0].pk in matched_objs:
              collected[tup] = 1
            elif collect == 'until':
              # cannot continue to search with this starting node
              to_remove.append(tup)

    if len(to_remove) > 0:
      obj_src = [tup for tup in obj_src if tup not in to_remove]

    visited = {}

    while len(obj_src) > 0:
      # prevent loops by removing previously encountered edges; because many
      # edges can lead to the same object, preventing revisit of edges rather
      # than objects avoids loops without missing out on an edge.
      new_src = [tup for tup in obj_src if tup not in visited]
      for tup in obj_src:
        visited[tup] = 1

      if len(new_src) == 0:
        break
      next_obj_src = Query._graph_step(new_src, model, step_f, filters, tree)
      # print "from %s\nreach %s" % (new_src, next_obj_src)

      if collect == 'terminal':
        next_demux = Query._graph_step([(obj, obj.pk) for obj, src in obj_src], model, step_f, filters)
        next_src = [t[1] for t in next_demux]

        for tup in obj_src:
          if tup[0].pk not in next_src:
            if tup not in collected:
              collected[tup] = 1
        obj_src = next_obj_src

      elif collect == 'search':
        reachable = Query._graph_step(obj_src, model, step_f, None)
        for tup in next_obj_src:
          if tup not in collected:
            collected[tup] = 1
        obj_src = list(set(reachable)-set(next_obj_src))

      elif collect == 'until':
        for tup in next_obj_src:
          if tup not in collected:
            collected[tup] = 1
        obj_src = next_obj_src

      else: # traversal
        reachable = Query._graph_step(obj_src, model, step_f, None)
        for tup in next_obj_src:
          if tup not in collected:
            collected[tup] = 1
        obj_src = reachable

    return collected.keys(), tree


  @staticmethod
  def _rel_step(obj_src, step):
    """
    Traverse a relationship, possibly recursively. Takes in and returns arrays
    of output, input object tuples. The input objects in the tuples are from
    start of the query, not start of this step.
    """

    tree = None

    if 'recursive' not in step or step['recursive'] is False:
      model = step['model']
      method = step['method']
      filters = step['filters']
      step_f = model_registry.get_manager(model).getattr(method)
      obj_src = Query._graph_step(obj_src, model, step_f, filters)

    else:
      obj_src, tree = Query._recursive_rel(obj_src, step)

    # print '%s: %d' % (step, len(obj_src))
    return obj_src, tree


  @staticmethod
  def _filter_by_subquery(obj_src, step):
    """
    Filters existing objects by the subquery.
    """

    subquery = step['subquery']
    having = step['having']
    #print 'sub %s, having %s' % (subquery, having)

    objects = [obj for obj, src in obj_src]
    subquery_res, last_model = Query._query(objects, subquery)
    #print 'res %s' % (subquery_res,)

    # take only the last result from subquery; grammar should enforce this.
    if len(subquery_res) > 0:
      assert(len(subquery_res) == 1)
      subquery_res = subquery_res[-1][0]

    subq_res_map = {}
    for sub_obj, sub_src in subquery_res:
      if sub_src not in subq_res_map:
        subq_res_map[sub_src] = []
      subq_res_map[sub_src].append(sub_obj)

    keep = []
    for obj, src in obj_src:
      result_from_subq = []
      if obj.pk in subq_res_map:
        result_from_subq = subq_res_map[obj.pk]

      if len(result_from_subq) > 0: # subquery has result
        # if no modifier to subquery, or said should have subquery results ('+' or '?')
        if having is None or having in ('+', '?'):
          keep.append((obj, src))

      if len(result_from_subq) == 0: # no subquery result
        # if said should not have subquery results ('-') or don't care ('?')
        if having in ('-', '?'):
          keep.append((obj, src))
          if having == '?':
            subquery_res.append((None, obj.pk))

    return keep, subquery_res


  @staticmethod
  def _or(obj_src, step):
    """
    Or results of multiple queries
    """

    or_queries = step['orquery']
    or_results = []

    for query in or_queries:
      objects = [obj for obj, src in obj_src]
      res, m = Query._query(objects, query)
      if len(res) > 0 and len(res[0][0]):
        or_results.append((res, m))

    models = list(set([r[1] for r in or_results]))
    if len(models) > 1:
      raise Exception("Different object types at end of OR query: %s" % (', '.join([str(x) for x in models]),))

    next_obj_src = []
    for res, m in or_results:
      next_obj_src.extend(res[0][0])

    return Query._extend_result(obj_src, next_obj_src)


  @staticmethod
  def _query(objects, query, demux_first=True):
    """
    Executes a query. A query consists of one or more subqueries. Each subquery
    is an array of model relationships. In most cases the outputs of a subquery
    becomes the inputs to the next query. 
    
    Input objects should be an array of model instances. Returns an array of
    subquery results. Each subquery result is an array of tuples. First member
    of tuple is output object from query. Second member of tuple is the pk of
    the input object that produced the output.
    """

    res = []
    more_results = True
    last_non_sub_index = -1
    last_tree = None

    if demux_first is True:
      obj_src = [(obj, obj.pk) for obj in objects]
    else:
      obj_src = [(obj, None) for obj in objects]

    for step in query:

      if ('join' in step and step['join'] is True) or\
         ('subquery' in step and (step['having'] is None or step['having'] == '?')):
        if more_results:
          res.append((obj_src, last_non_sub_index, last_tree))
          last_non_sub_index = len(res)-1
          more_results = False
          obj_src = list(set([(obj, obj.pk) for obj, src in obj_src]))

      if 'orquery' in step:
        #print 'orquery %s' % step
        obj_src = Query._or(obj_src, step)
        #print 'completed orquery'
        more_results = True

      elif 'subquery' in step:
        #print 'subquery %s' % step
        obj_src, subquery_res = Query._filter_by_subquery(obj_src, step)
        #print 'completed subquery'

        if step['having'] is None or step['having'] == '?': 
          # add subquery result to results, even if there are no results from subquery
          res.append((subquery_res, last_non_sub_index, last_tree))
          # don't increase last_non_sub_index, so caller knows next query
          # should still join with the last non sub query results.
          more_results = False

      else:
        #print 'query: %s' % step
        obj_src, last_tree = Query._rel_step(obj_src, step)
        #print 'completed query'
        more_results = True

    if more_results:
      res.append((obj_src, last_non_sub_index, last_tree))

    # last model, can be None if left join and got no data
    t = None
    for obj, src in obj_src:
      if obj is not None:
        t = obj.__class__
        if hasattr(t, '_deferred') and t._deferred:
          t = t.__base__
        break

    return res, t


  def __call__(self):
    """
    Executes the current query. Returns array of tuples; first member of tuple
    is output object from query, second member of tuple is the object from the
    first step of the query that produced the output object. Also returns
    current model at end of query, which may be different than model of the
    last result if last result is a filter query.
    """

    objects = list(self.__get_objects())
    return Query._query(objects, self.__steps, demux_first=False)
