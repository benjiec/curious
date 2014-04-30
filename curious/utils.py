import time

# for development/debugging
def report_time(f):
  def wrap(*args, **kwargs):
    t = time.time()
    r = f(*args, **kwargs)
    print '%s.%s: %.4f' % (f.__module__, f.func_name, time.time()-t)
    return r
  return wrap
