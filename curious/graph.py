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

def _valid_django_rel(rel_obj_descriptor):
  return type(rel_obj_descriptor) in (ReverseSingleRelatedObjectDescriptor,
                                      ForeignRelatedObjectsDescriptor,
                                      ReverseManyRelatedObjectsDescriptor,
                                      ManyRelatedObjectsDescriptor)

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
      print type(rel_obj_descriptor)
      raise Exception("Cannot handle related object descriptor %s." % rel_obj_descriptor)

  def _get_related_objects(instances, filters=None):
    queryset = None

    # functioning defining a relationship
    if type(rel_obj_descriptor) in (types.FunctionType, types.MethodType):
      queryset = rel_obj_descriptor(instances)

    # FK from instance to a related object
    elif type(rel_obj_descriptor) == ReverseSingleRelatedObjectDescriptor:
      queryset = rel_obj_descriptor.get_prefetch_queryset(instances)

    # the following three relationships have the same logic, but because they
    # use separately defined descriptor classes in django, they get separate if
    # clauses below, for clarity and in case of changes in django.

    # reverse FK from instance to related objects with FK to the instance
    elif type(rel_obj_descriptor) == ForeignRelatedObjectsDescriptor:
      queryset = rel_obj_descriptor.__get__(instance).get_prefetch_queryset(instances)[0]

    # M2M from instance to related objects
    elif type(rel_obj_descriptor) == ReverseManyRelatedObjectsDescriptor:
      queryset = rel_obj_descriptor.__get__(instance).get_prefetch_queryset(instances)[0]

    # reverse M2M from instance to related objects
    elif type(rel_obj_descriptor) == ManyRelatedObjectsDescriptor:
      queryset = rel_obj_descriptor.__get__(instance).get_prefetch_queryset(instances)[0]

    if queryset:
      if filters:
        if '__exclude__' in filters:
          ff = {k: v for k, v in filters.iteritems() if k != '__exclude__'}
          return queryset.exclude(**ff)
        else:
          return queryset.filter(**filters)
      else:
        return queryset
    return []

  # turn prefetching OFF
  def get_related_objects(instances, filters=None):
    r = _get_related_objects(instances, filters=filters)
    if type(r) == QuerySet:
      r._prefetch_done = True
    return r

  return get_related_objects


def step_recursive(nodes, attr, loop_condition_f, continue_f=None, terminal_f=None, hop=0):
  """
  Recursively traverse related attr. At each node (starting with nodes), calls
  loop_condition_f, then calls continue_f or terminal_f depending on the result
  of loop_condition_f.

  loop_condition_f: lambda node, hops
  continue_f: lambda node
  terminal_f: lambda node
  """

  nodes = list(nodes) if type(nodes) == QuerySet else nodes
  nodes = [nodes] if type(nodes) not in [type([]), type((0,))] else nodes

  continuing_nodes = []
  for node in nodes:
    if not loop_condition_f or loop_condition_f(node, hop):
      if continue_f:
        continue_f(node)
      continuing_nodes.append(node)
    else:
      if terminal_f:
        terminal_f(node)

  if len(continuing_nodes) == 0:
    return

  f = get_related_obj_accessor(attr, continuing_nodes[0], True)
  if f:  
    nodes = f(continuing_nodes)
    step_recursive(nodes, attr, loop_condition_f, continue_f, terminal_f, hop+1)


def steps(nodes, attrs, filterl=None):
  """
  Starting with a node, walk one step at a time, using each of related attrs.
  Does all queries in batch so the number of queries is number of
  relationships.
  """

  attrs = [attrs] if type(attrs) not in [type([]), type((0,))] else attrs
  nodes = list(nodes) if type(nodes) == QuerySet else nodes
  nodes = [nodes] if type(nodes) not in [type([]), type((0,))] else nodes
  if filterl is not None:
    filterl = [filterl] if type(filterl) not in [type([]), type((0,))] else filterl

  if filterl is not None:
    if len(attrs) != len(filterl):
      raise Exception('Attribute list and filter list must have same length')

  if len(nodes) == 0:
    return []
  if len(attrs) == 0:
    return nodes

  for i, attr in enumerate(attrs):
    f = get_related_obj_accessor(attr, nodes[0])
    if filterl is not None:
      filters = filterl[i]
    else:
      filters = None
    nodes = f(nodes, filters=filters)
    if len(nodes) == 0:
      return []

  return nodes
