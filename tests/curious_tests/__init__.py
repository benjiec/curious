def _d(instance):
  if instance is None:
    return instance
  t = type(instance)
  if hasattr(t, '_deferred') and t._deferred:
    t = t.__base__
  return (t, instance.pk)

def assertQueryResultsEqual(tester, results, expected):
  """
  Test query results, with deferred model instances, equal to expected results,
  typically specified with real instances.
  """

  # convert all to (real model, id) pairs

  results = [(_d(tup[0]), tup[1]) for tup in results]
  expected = [(_d(tup[0]), tup[1]) for tup in expected]
  tester.assertItemsEqual(results, expected)
