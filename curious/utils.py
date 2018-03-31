from functools import wraps
import time
from . import settings

# for development/debugging
def report_time(f):
  @wraps(f)
  def wrap(*args, **kwargs):
    t = time.time()
    r = f(*args, **kwargs)
    if settings.DEBUG:
      print '%s.%s: %.4f' % (f.__module__, f.func_name, time.time()-t)
    return r
  return wrap
