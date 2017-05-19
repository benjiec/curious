import time
import os

# for development/debugging
def report_time(f):
  DEBUG = os.environ.get('DEBUG')
  def wrap(*args, **kwargs):
    t = time.time()
    r = f(*args, **kwargs)
    if DEBUG:
      print '%s.%s: %.4f' % (f.__module__, f.func_name, time.time()-t)
    return r
  return wrap
