from .parser import Parser
from curious import model_registry
from curious.graph import steps, step_recursive


class Query(object):

  def __init__(self, query):
    self.__query = query
    parser = Parser(query)
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
  def _recursive_rel(objects, step_f, filters, need_terminal):
    """
    Traverse a relationship recursively. Returns collected objects, either loop
    terminating objects or loop continuing objects.
    """

    collected = []
    while len(objects) > 0:
      # get objects that can continue, w/ filters
      next_objects = steps(objects, step_f, filters)

      if need_terminal:
        # get all reachable objects, w/o filtering
        reachable = steps(objects, step_f)
        for obj in reachable:
          if obj not in next_objects:
            if obj not in collected:
              collected.append(obj)
      else:
        for obj in next_objects:
          if obj not in collected:
            collected.append(obj)
      objects = next_objects

    return collected


  @staticmethod
  def _rel_step(objects, step):
    """
    Traverse a relationship, possibly recursively. Returns next set of objects.
    """

    model = step['model']
    method = step['method']
    filters = step['filters']

    # check if type matches existing object type
    if len(objects) and type(objects[0]) != model_registry.getclass(model):
      raise Exception('Type mismatch when executing query: expecting "%s", got "%s"' %
                      (model, type(objects[0])))

    step_f = model_registry.getattr(model, method)

    if 'recursive' not in step or step['recursive'] is False:
      objects = steps(objects, step_f, filters)

    else:
      need_terminal = 'collect' in step and step['collect'] == 'terminal'
      objects = Query._recursive_rel(objects, step_f, filters, need_terminal)

    # print '%s: %d' % (step, len(objects))
    return objects


  @staticmethod
  def _filter_by_subquery(objects, step):
    """
    Filters existing objects by the subquery.
    """

    subquery = step['subquery']
    having = step['having']

    keep = []
    for object in objects:
      subquery_objects = Query._query([object], subquery)
      if (having is True and len(subquery_objects) > 0) or\
         (having is False and len(subquery_objects) == 0):
        keep.append(object)

    return keep


  @staticmethod
  def _step(objects, step):
    """
    Executes one step from list of objects, return new objects for next step.
    """

    if 'subquery' in step:
      # print 'subquery %s' % step
      return Query._filter_by_subquery(objects, step)
    else:
      # print 'rel %s' % step
      return Query._rel_step(objects, step)


  @staticmethod
  def _query(objects, query):
    """
    Executes a query. A query is an array whose elements are model
    relationships or subqueries.
    """

    for step in query:
      if len(objects) > 0:
        objects = Query._step(objects, step)
      else:
        return []
    return objects


  def __call__(self):
    objects = list(self.__get_objects())
    return Query._query(objects, self.__steps)
