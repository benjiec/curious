import types
import django.db.models
from .graph import _valid_django_rel


class ModelRegistry(object):
  def __init__(self):
    self.__name_shortcuts = {}
    self.__models = {}
    self.__model_field_excludes = {}
    self.__model_url_funcs = {}

  @staticmethod
  def model_name(model_class):
    return '%s__%s' % (model_class._meta.app_label, model_class.__name__)

  def register(self, model):
    if type(model) == types.ModuleType:
      for name in dir(model):
        cls = getattr(model, name)
        try:
          if issubclass(cls, django.db.models.Model) and cls._meta.abstract is False:
            model_name = ModelRegistry.model_name(cls)
            self.__models[model_name] = dict(cls=cls, allowed=[], disallowed=[])
            if cls.__name__ not in self.__name_shortcuts:
              self.__name_shortcuts[cls.__name__] = []
            self.__name_shortcuts[cls.__name__].append(model_name)
        except:
          pass
    else:
      if model._meta.abstract is False:
        model_name = ModelRegistry.model_name(model)
        self.__models[model_name] = dict(cls=model, allowed=[], disallowed=[])
        if model.__name__ not in self.__name_shortcuts:
          self.__name_shortcuts[model.__name__] = []
        self.__name_shortcuts[model.__name__].append(model_name)

  def translate_name(self, name):
    if name in self.__models:
      model_name = name
    else:
      if name in self.__name_shortcuts:
        if len(self.__name_shortcuts[name]) != 1:
          raise Exception('Ambiguous model name "%s": can match to %s' %
                          (name, ', '.join(self.__name_shortcuts[name])))
        else:
          model_name = self.__name_shortcuts[name][0]
      else:
        raise Exception("Don't know about model %s" % name)
    return model_name

  def add_custom_rel(self, name, rel):
    model_name = self.translate_name(name)
    self.__models[model_name]['allowed'].append(rel)

  def disallow_rel(self, name, rel):
    model_name = self.translate_name(name)
    self.__models[model_name]['disallowed'].append(rel)

  def add_model_url_func(self, name, f):
    model_name = self.translate_name(name)
    self.__model_url_funcs[model_name] = f

  def add_model_field_exclude(self, name, f):
    model_name = self.translate_name(name)
    if model_name not in self.__model_field_excludes:
      self.__model_field_excludes[model_name] = []
    self.__model_field_excludes[model_name].append(f)

  @property
  def model_names(self):
    return [k for k in self.__models]

  def is_rel_allowed(self, cls, f):
    model_name = ModelRegistry.model_name(cls)
    if _valid_django_rel(getattr(cls, f)) and\
       not f in self.__models[model_name]['disallowed']:
      return True
    return f in self.__models[model_name]['allowed']

  def getclass(self, name):
    model_name = self.translate_name(name)
    return self.__models[model_name]['cls']

  def getname(self, cls):
    try:
      model_name = self.translate_name(cls.__name__)
      return cls.__name__
    except:
      return ModelRegistry.model_name(cls)

  def geturl(self, name, obj):
    model_name = self.translate_name(name)
    if model_name in self.__model_url_funcs:
      return self.__model_url_funcs[model_name](obj)
    return None

  def getexcludes(self, name):
    model_name = self.translate_name(name)
    if model_name in self.__model_field_excludes:
      return self.__model_field_excludes[model_name]
    return []

  def getattr(self, name, method):
    cls = self.getclass(name)
    if not hasattr(cls, method):
      raise Exception('Unknown attribute "%s" in "%s"' % (method, name))
    if not self.is_rel_allowed(cls, method):
      raise Exception('Not allowed to call "%s"' % method)
    return getattr(cls, method)

model_registry = ModelRegistry()
