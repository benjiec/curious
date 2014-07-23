from curious import deferred_to_real

def remote_fk(from_model_fk_field, to_model):
  @staticmethod
  def rel_f(instances, filter_f):
    instances = deferred_to_real(instances)
    q = to_model.objects.filter(pk__in=[getattr(instance, from_model_fk_field) for instance in instances])
    q = filter_f(q)

    to_from = {}

    for instance in instances:
      k = getattr(instance, from_model_fk_field)
      if k not in to_from:
        to_from[k] = []
      to_from[k].append(instance)

    r = []
    for obj in q:
      for src in to_from[obj.pk]:
        r.append((obj, src.pk))
    return r

  return rel_f


def remote_reverse_fk(to_model_fk_field, to_model):
  @staticmethod
  def rel_f(instances, filter_f):
    arg = {}
    arg['%s__in' % to_model_fk_field] = [instance.pk for instance in instances]
    q = to_model.objects.filter(**arg)
    q = filter_f(q)
    return [(obj, getattr(obj, to_model_fk_field)) for obj in q]

  return rel_f
