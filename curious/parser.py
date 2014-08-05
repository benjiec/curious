from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor

from time import mktime
from datetime import datetime
import parsedatetime

from .grammar import QUERY_PEG


class Parser(object):
  def __init__(self, code):
    self.object_query = {}
    self.subqueries = []

    # parsing:
    grammar = Grammar(QUERY_PEG)
    self.__nodes = grammar.parse(code)
    self._translate()

  def _translate(self):
    ast_builder = ASTBuilder()
    query = ast_builder.visit(self.__nodes)
    self.object_query = query[0]
    self.subqueries = query[1:]


from parsimonious.nodes import NodeVisitor


class ASTBuilder(NodeVisitor):

  def visit_object_query(self, node, (model, filters)):
    return dict(model=model, method=None, filters=filters)

  def visit_one_rel(self, node, (model, _1, method, filters)):
    if type(filters) != list:
      filters = None
    else:
      filters = filters[0]
    return dict(model=model, method=method, filters=filters)

  def visit_filter_or_id(self, node, f_or_id):
    return f_or_id[0]

  def visit_id_arg(self, node, (_1, _2, id, _3, _4)):
    return [dict(method='filter', kwargs=dict(id=id))]

  def visit_filters(self, node, (f, more_filters)):
    filters = []
    if type(f) == list:
      f[0]['method'] = 'filter'
      filters.append(f[0])
    if type(more_filters) == list:
      filters.extend(more_filters[0])
    return filters

  def visit_name_filters(self, node, (f, more_filters)):
    filters = []
    filters.append(f)
    if type(more_filters) == list:
      filters.extend(more_filters)
    return filters

  def visit_name_filter(self, node, (_1, method, f)):
    f['method'] = method
    return f

  def visit_filter_group(self, node, (_1, args, _2)):
    return args

  def visit_model(self, node, v):
    return v[0]

  def visit_filter_args(self, node, args):
    if type(args[0]) == dict:
      return {'kwargs': args[0]}
    return {'field': args[0]}

  def visit_filter_kvs(self, node, (_1, arg, more_args, _2)):
    d = arg
    for a in more_args:
      d.update(a)
    return d

  def visit_arg(self, node, (arg_name, _1, equal, _2, value)):
    d = {}
    d[arg_name] = value
    return d

  def visit_another_arg(self, node, (_1, comma, _2, arg)):
    return arg

  def visit_identifier(self, node, _):
    return node.text

  def visit_id(self, node, _):
    return node.text

  def visit_values(self, node, val):
    return val[0]

  def visit_array_value(self, node, (br1, _1, value, more_values, _2, br2)):
    if type(more_values) != list:
      more_values = []
    return [value]+more_values

  def visit_another_val(self, node, (_1, comma, _2, value)):
    return value

  def visit_value(self, node, value):
    return value[0]

  def visit_bool(self, node, _):
    return True if node.text == "True" else False

  def visit_null(self, node, _):
    return None

  def visit_int(self, node, _):
    return int(node.text)

  def visit_float(self, node, _):
    return float(node.text)

  def visit_string(self, node, (t, s)):
    if type(t) == list:
      c = parsedatetime.Calendar()
      t = c.parse(s)
      return datetime.fromtimestamp(mktime(t[0]))
    return s

  def visit_q_string(self, node, s):
    return s[0]

  def visit_dq_string(self, node, (q0, v, q1)):
    return v.text

  def visit_sq_string(self, node, (q0, v, q1)):
    return v.text

  def generic_visit(self, node, visited_children):
    return visited_children or node

  # steps

  def visit_recursion(self, node, _):
    return node.text

  def _handle_recursion(self, d, recursion):
    if type(recursion) == list:
      d['recursive'] = True
      if recursion[0] == '$':
        d['collect'] = 'terminal'
      elif recursion[0] == '?':
        d['collect'] = 'search'
      elif recursion[0] == '*':
        d['collect'] = 'until'
      else:
        d['collect'] = 'all'

  def visit_la_modifier(self, node, _):
    return node.text

  def visit_chain(self, node, (step, more_steps)):
    chain = [step]
    for s in more_steps:
      chain.append(s)
    return chain

  def visit_another_step(self, node, (_1, step)):
    return step

  def visit_step(self, node, q):
    return q[0]

  def visit_step_rl(self, node, (step, recursion, la)):
    d = dict(chain=[step])
    self._handle_recursion(d, recursion)
    if type(la) == list:
      d['look_ahead'] = la
    return d

  def visit_group(self, node, (_1, chain, _2)):
    return chain

  def visit_or_step(self, node, (_p1, step1, _s1, _or, _s2, step2, more_steps, _p2)):
    r = dict(or_chain=[step1, step2])
    if type(more_steps) == list:
      r['or_chain'].extend(more_steps)
    return r

  def visit_another_or(self, node, (_s1, _or, _s2, step)):
    return step

  def visit_look_ahead(self, node, (_s1, modifier, _1, chain, _2)):
    having = modifier
    return dict(chain=chain, having=having, join=False)

  # joins

  def visit_join(self, node, join):
    return join[0]

  def visit_inner_join(self, node, (_s1, _comma, _s2, chain)):
    return dict(chain=chain, join=True)

  def visit_recur_join(self, node, (_s1, _comma, _s2, _p1, chain, joins, _p2, recursion)):
    if type(joins) == list:
      chain += joins
    d = dict(chain=chain, join=True)
    self._handle_recursion(d, recursion)
    return d

  def visit_left_join(self, node, (_s1, _lj, _p1, chain, _p2, recursion)):
    d = dict(chain=chain, having='?', join=False)
    self._handle_recursion(d, recursion)
    return d

  def visit_query(self, node, (obj_query, la, _1, chain, joins, _2)):
    d = dict(chain=obj_query)
    if type(la) == list:
      d['look_ahead'] = la
    r = [d]
    if type(chain) == list:
      r += chain[0]
    if type(joins) == list:
      r += joins
    return r
