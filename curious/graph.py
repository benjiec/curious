"""
Traversing a graph of Django models, using FK and M2M relationships as edges. A
model can also explicitly define a relationship via a static method that takes
in model instances and returns a QuerySet for fetching the related objects for
these instances.
"""

import types
from django.db.models.query import QuerySet
from django.db.models.fields.related import ReverseSingleRelatedObjectDescriptor
from django.db.models.fields.related import ForeignRelatedObjectsDescriptor
from django.db.models.fields.related import ReverseManyRelatedObjectsDescriptor
from django.db.models.fields.related import ManyRelatedObjectsDescriptor


# The following django model attributes are relationships we can traverse
def _valid_django_rel(rel_obj_descriptor):
  return type(rel_obj_descriptor) in (ReverseSingleRelatedObjectDescriptor,
                                      ForeignRelatedObjectsDescriptor,
                                      ReverseManyRelatedObjectsDescriptor,
                                      ManyRelatedObjectsDescriptor)


# Use this attr of a query output object to determine the input object
# producing the output object using the query.
INPUT_ATTR_PREFIX = '_prefetch_related_val_'

def get_related_obj_accessor(rel_obj_descriptor, instance, allow_missing_rel=False):
  """
  From a related object descriptor (there are a few types of descriptors
  defined in django.db.models.fields.related), build a function that takes in
  multiple instances and return the related objects for all the instances.

  The instance variable is an example instance, required by Django to construct
  a related object manager; it does not affect the query produced by the
  returned function.
  """

  if not _valid_django_rel(rel_obj_descriptor) and\
     type(rel_obj_descriptor) not in (types.FunctionType, types.MethodType):
    if allow_missing_rel:
      return None
    else:
      raise Exception("Cannot handle related object descriptor %s." % rel_obj_descriptor)

  def get_related_objects(instances, filters=None):
    queryset = None

    def apply_filters(q):
      if filters is not None:
        if '__exclude__' in filters:
          ff = {k: v for k, v in filters.iteritems() if k != '__exclude__'}
          return q.exclude(**ff)
        else:
          return q.filter(**filters)
      return q

    # functioning defining a relationship
    if type(rel_obj_descriptor) in (types.FunctionType, types.MethodType):
      return rel_obj_descriptor(instances, apply_filters)

    # FK from instance to a related object
    elif type(rel_obj_descriptor) == ReverseSingleRelatedObjectDescriptor:
      table = instances[0]._meta.db_table
      related_table = rel_obj_descriptor.field.related_field.model._meta.db_table
      #print 'starting with %s, related %s' % (table, related_table)
      if table == related_table:
        # XXX hack: assuming django uses T2 for joining two tables of same name
        table = 'T2'
      queryset = rel_obj_descriptor.get_prefetch_queryset(instances)[0]\
                                   .extra(select={INPUT_ATTR_PREFIX: '%s.id' % table})
      #print queryset.query
      queryset._prefetch_done = True

    # reverse FK from instance to related objects with FK to the instance
    elif type(rel_obj_descriptor) == ForeignRelatedObjectsDescriptor:
      column = rel_obj_descriptor.related.field.column
      table = instances[0]._meta.db_table
      queryset = rel_obj_descriptor.__get__(instance).get_prefetch_queryset(instances)[0]\
                                   .extra(select={INPUT_ATTR_PREFIX: '%s' % column})
      queryset._prefetch_done = True

    # M2M from instance to related objects
    elif type(rel_obj_descriptor) == ReverseManyRelatedObjectsDescriptor:
      queryset = rel_obj_descriptor.__get__(instance).get_prefetch_queryset(instances)[0]
      queryset._prefetch_done = True

    # reverse M2M from instance to related objects
    elif type(rel_obj_descriptor) == ManyRelatedObjectsDescriptor:
      queryset = rel_obj_descriptor.__get__(instance).get_prefetch_queryset(instances)[0]
      queryset._prefetch_done = True

    if queryset:
      return apply_filters(queryset)

    return []

  return get_related_objects


def step_one(nodes, attr, filters=None):
  """
  Traverse one relationship on list of nodes. Returns output, input tuple
  array, where input is the pk of the node producing the output object.
  """

  nodes = list(nodes) if type(nodes) == QuerySet else nodes
  nodes = [nodes] if type(nodes) not in [type([]), type((0,))] else nodes

  if len(nodes) == 0:
    return []
  if attr is None:
    return nodes

  f = get_related_obj_accessor(attr, nodes[0])
  nodes = f(nodes, filters=filters)

  if len(nodes) == 0:
    return []

  # already in output, input tuple format
  elif type(nodes[0]) == tuple:
    return nodes

  else:
    nodes_with_src = []
    for node in nodes:
      src = None
      for a in dir(node):
        if a.startswith(INPUT_ATTR_PREFIX):
          src = getattr(node, a)
          break
      nodes_with_src.append((node, src))

    return nodes_with_src
