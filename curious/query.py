from .parser import Parser
from curious import model_registry
from curious.graph import step_one


class Query(object):

  def __init__(self, query):
    parser = Parser(query)
    self.__query = query
    self.__obj_query = parser.object_query
    self.__steps = parser.steps
    self.__validate()


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
    if '__id__' in filters:
      filters['pk'] = filters['__id__']
      del filters['__id__']
    if method is None:
      cls = model_registry.getclass(model)
      if '__exclude__' in filters:
        ff = {k: v for k, v in filters.iteritems() if k != '__exclue__'}
        return cls.objects.exclude(**ff)
      else:
        x = cls.objects.filter(**filters)
        return x
    else:
      f = model_registry.getattr(model, method)
      return f(**filters)


  @staticmethod
  def _graph_step(obj_src, step_f, filters):
    """
    Traverse one step on the graph. Takes in and returns arrays of output,
    input object tuples. The input objects in the tuples are from start of the
    query, not start of this step.
    """

    next_obj_src = step_one([obj for obj, src in obj_src], step_f, filters)

    keep = []
    for next_obj, next_src in next_obj_src:
      # find next_src in original obj_src
      for obj, src in obj_src:
        if obj.pk == next_src:
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

    while len(obj_src) > 0:
      # get objects that can continue, w/ filters
      next_obj_src = Query._graph_step(obj_src, step_f, filters)

      if need_terminal:
        # get all reachable objects, w/o filtering
        reachable = Query._graph_step(obj_src, step_f)
        for tup in reachable:
          if tup not in next_obj_src:
            if tup not in collected:
              collected.append(tup)
      else:
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
    if len(obj_src) and type(obj_src[0][0]) != model_registry.getclass(model):
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

    objects = [obj for obj, src in obj_src]
    subquery_res = Query._query(objects, subquery)
    if len(subquery_res) > 0:
      # only care about objects from the last join query
      subquery_res = subquery_res[-1]

    keep = []
    for obj, src in obj_src:
      res = [sub_obj for sub_obj, sub_src in subquery_res if sub_src == obj]
      if (having is True and len(res) > 0) or\
         (having is False and len(res) == 0):
        keep.append((obj, src))

    return keep


  @staticmethod
  def _step(obj_src, step):
    """
    Executes one step, which can either be a relation, or a subquery filter.
    Takes in and returns arrays of output, input object tuples.
    """

    if 'subquery' in step:
      # print 'subquery %s' % step
      return Query._filter_by_subquery(obj_src, step)
    else:
      # print 'rel %s' % step
      return Query._rel_step(obj_src, step)


  @staticmethod
  def _query(objects, query):
    """
    Executes a query. A query is an array whose elements are model
    relationships or subqueries. 
    
    Input objects should be an array of model
    instances. Returns array of tuples; first member of tuple is output object
    from query, second member of tuple is the pk of the input object that
    produced the output.
    """

    res = []

    obj_src = [(obj, obj.pk) for obj in objects]
    for step in query:
      if len(obj_src) == 0:
        return []

      if 'join' in step:
        res.append(obj_src)
        obj_src = list(set([(obj, obj.pk) for obj, src in obj_src]))

      obj_src = Query._step(obj_src, step)

    if len(obj_src) == 0:
      return []
    res.append(obj_src)
    return res


  def __call__(self):
    """
    Executes the current query. Returns array of tuples; first member of tuple
    is output object from query, second member of tuple is the object from the
    first step of the query that produced the output object.
    """

    objects = list(self.__get_objects())
    return Query._query(objects, self.__steps)
