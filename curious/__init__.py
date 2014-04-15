import types
import django.db.models
from .graph import _valid_django_rel


class ModelRegistry(object):
  def __init__(self):
    self.__models = {}

  def register(self, model):
    if type(model) == types.ModuleType:
      for name in dir(model):
        cls = getattr(model, name)
        try:
          if issubclass(cls, django.db.models.Model):
            self.__models[name] = [cls, []]
        except:
          pass
    else:
      self.__models[model.__name__] = [model, []]

  def add_custom_rel(self, model_name, rel):
    if model_name not in self.__models:
      raise Exception('Please register model before custom relationship')
    self.__models[model_name][1].append(rel)

  def allow_rel(self, model_name, f):
    return f in self.__models[model_name][1]

  @property
  def model_names(self):
    return [k for k in self.__models]

  def getclass(self, model_name):
    if model_name not in self.__models:
      raise Exception('Unknown model "%s"' % model_name)
    return self.__models[model_name][0]

  def getattr(self, model_name, method):
    cls = self.getclass(model_name)
    if not hasattr(cls, method):
      raise Exception('Unknown attribute "%s" in "%s"' % (method, model_name))
    f = getattr(cls, method)
    if not _valid_django_rel(f) and not self.allow_rel(model_name, method):
      raise Exception('Not allowed to call "%s"' % method)
    return f

model_registry = ModelRegistry()
