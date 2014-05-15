from .parser import Parser
from curious import model_registry
from curious.graph import traverse, mk_filter_function


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
      if 'subquery' in rel:
        Query._validate(rel['subquery'])
      else:
        model = rel['model']
        method = rel['method']
        if method is None:
          model_registry.getclass(model)
        else:
          model_registry.getattr(model, method)


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
      cls = model_registry.getclass(model)
      q = cls.objects.all()
      q = filter_f(q)
      return q
    else:
      f = model_registry.getattr(model, method)
      return f(filter_f)


  @staticmethod
  def _graph_step(obj_src, step_f, filters):
    """
    Traverse one step on the graph. Takes in and returns arrays of output,
    input object tuples. The input objects in the tuples are from start of the
    query, not start of this step.
    """

    next_obj_src = traverse([obj for obj, src in obj_src], step_f, filters)

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
  def _recursive_rel(obj_src, step_f, filters, need_terminal):
    """
    Traverse a relationship recursively. Collected objects, either loop
    terminating objects or loop continuing objects. Returns arrays of output,
    input object tuples. The input objects in the tuples are from start of the
    query, not start of this step.
    """

    collected = []

    if need_terminal is False:
      # if getting all intermediate nodes, then also keep starting nodes
      for tup in obj_src:
        collected.append(tup)

    while len(obj_src) > 0:
      next_obj_src = Query._graph_step(obj_src, step_f, filters)

      if need_terminal and (filters is None or filters == []):
        # traverse one step from last set of nodes
        src = [(t[0], t[0].pk) for t in obj_src]
        progressed = Query._graph_step(src, step_f, filters)
        progressed = [t[1] for t in progressed]
        for tup in obj_src:
          # if we didn't progress, than collect
          if tup[0].pk not in progressed:
            if tup not in collected:
              collected.append(tup)

      elif need_terminal:
        # get all reachable objects, w/o filtering
        reachable = Query._graph_step(obj_src, step_f, None)
        for tup in reachable:
          if tup not in next_obj_src:
            if tup not in collected:
              collected.append(tup)

      else: # need all intermediate
        for tup in next_obj_src:
          if tup not in collected:
            collected.append(tup)

      obj_src = next_obj_src

    return collected


  @staticmethod
  def _rel_step(obj_src, step):
    """
    Traverse a relationship, possibly recursively. Takes in and returns arrays
    of output, input object tuples. The input objects in the tuples are from
    start of the query, not start of this step.
    """

    model = step['model']
    method = step['method']
    filters = step['filters']

    # check if type matches existing object type
    if len(obj_src):
      t = type(obj_src[0][0])
      if t._deferred:
        t = t.__base__
      if t != model_registry.getclass(model):
        raise Exception('Type mismatch when executing query: expecting "%s", got "%s"' %
                        (model, type(obj_src[0][0])))

    step_f = model_registry.getattr(model, method)

    if 'recursive' not in step or step['recursive'] is False:
      obj_src = Query._graph_step(obj_src, step_f, filters)

    else:
      need_terminal = 'collect' in step and step['collect'] == 'terminal'
      obj_src = Query._recursive_rel(obj_src, step_f, filters, need_terminal)

    # print '%s: %d' % (step, len(obj_src))
    return obj_src


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

    if len(subquery_res) > 0:
      assert(len(subquery_res) == 1)
      subquery_res = subquery_res[-1]

    keep = []
    for obj, src in obj_src:
      result_from_subq = [sub_obj for sub_obj, sub_src in subquery_res if sub_src == obj.pk]
      if (having is True and len(result_from_subq) > 0) or\
         (having is False and len(result_from_subq) == 0):
        keep.append((obj, src))

    return keep, subquery_res


  @staticmethod
  def _query(objects, query):
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

    obj_src = [(obj, obj.pk) for obj in objects]
    for step in query:
      if len(obj_src) == 0:
        return [], None

      if 'join' in step and step['join'] is True:
        res.append(obj_src)
        more_results = False
        obj_src = list(set([(obj, obj.pk) for obj, src in obj_src]))

      if 'subquery' in step:
        # print 'subquery %s' % step
        obj_src, subquery_res = Query._filter_by_subquery(obj_src, step)
        if 'join' in step and step['join'] is True:
          # add subquery result to results
          res.append(subquery_res)
          more_results = False
          # link subquery res to pre subquery result, so we can continue query
          # from pre subquery result
          new_obj_src = []
          for obj, src in obj_src:
            new_obj_src += [(obj, sub_obj.pk) for sub_obj, sub_src in subquery_res if sub_src == obj.pk]
          obj_src = new_obj_src

      else:
        obj_src = Query._rel_step(obj_src, step)
        more_results = True

    if len(obj_src) == 0:
      return [], None

    if more_results:
      res.append(obj_src)

    t = obj_src[0][0].__class__
    if t._deferred:
      t = t.__base__
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
    return Query._query(objects, self.__steps)
