import os
from webassets import Bundle
from webassets import Environment

css = Bundle('curious/src/css/app.css',
             output='curious/dist/curious.css')

js  = Bundle('curious/src/js/*.js',
             output='curious/dist/curious.js')

jsm = Bundle('curious/src/js/*.js', filters='jsmin',
             output='curious/dist/curious.min.js')

jst = Bundle('curious/src/html/*.html', filters='jst',
             output='curious/dist/curious_jst.js')

assets_env = Environment('./curious/static')
try:
  os.mkdir('.webassets-cache')
except:
  pass
assets_env.cache = '.webassets-cache'
assets_env.register('css', css)
assets_env.register('js', js)
assets_env.register('jsmin', jsm)
assets_env.register('jst', jst)

if __name__ == "__main__":
  from webassets.script import CommandLineEnvironment
  import logging

  log = logging.getLogger('webassets')
  log.addHandler(logging.StreamHandler())
  log.setLevel(logging.DEBUG)
  cmdenv = CommandLineEnvironment(assets_env, log)
  cmdenv.build()
