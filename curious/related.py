from curious import deferred_to_real

def remote_fk(from_model_fk_field, to_model, to_model_field=None):
  to_model_field = 'pk' if to_model_field is None else to_model_field

  @staticmethod
  def rel_f(instances, filter_f):
    instances = deferred_to_real(instances)
    c = {}
    c['%s__in' % to_model_field] = [getattr(instance, from_model_fk_field) for instance in instances]
    q = to_model.objects.filter(**c)
    if to_model_field not in ['pk', 'id']:
      f = {}
      f[to_model_field] = to_model_field
      q = q.extra(select=f)
    q = filter_f(q)

    to_from = {}

    for instance in instances:
      k = getattr(instance, from_model_fk_field)
      if k not in to_from:
        to_from[k] = []
      to_from[k].append(instance)

    r = []
    for obj in q:
      for src in to_from[getattr(obj, to_model_field)]:
        r.append((obj, src.pk))
    return r

  return rel_f


def remote_reverse_fk(to_model_fk_field, to_model, from_model_field=None):
  from_model_field = 'pk' if from_model_field is None else from_model_field

  @staticmethod
  def rel_f(instances, filter_f):
    arg = {}
    arg['%s__in' % to_model_fk_field] = [getattr(instance, from_model_field) for instance in instances]
    q = to_model.objects.filter(**arg)
    if to_model_fk_field not in ['pk', 'id']:
      f = {}
      f[to_model_fk_field] = to_model_fk_field
      q = q.extra(select=f)
    q = filter_f(q)

    to_from = {}

    for instance in instances:
      k = getattr(instance, from_model_field)
      if k not in to_from:
        to_from[k] = []
      to_from[k].append(instance)

    r = []
    q = list(q)
    for obj in q:
      for src in to_from[getattr(obj, to_model_fk_field)]:
        r.append((obj, src.pk))
    return r

  return rel_f
