from unittest import TestCase

from curious import ModelRegistry

from curious_tests import models


class TestModelRegistry(TestCase):

  def setUp(self):
    self.model_registry = ModelRegistry()

  def tearDown(self):
    self.model_registry.clear()
    del self.model_registry

  def test_register(self):
    self.model_registry.register(models.Person)

    self.assertEqual([['curious_tests__Person']], [self.model_registry.model_names])

  def test_register_abstract(self):
    self.model_registry.register(models.Person)
    self.model_registry.register(models.LivingThing)

    self.assertEqual([['curious_tests__Person']], [self.model_registry.model_names])

  def test_unregister(self):
    self.model_registry.register(models.Person)
    self.model_registry.unregister('Person')
    self.assertEqual([[]], [self.model_registry.model_names])
