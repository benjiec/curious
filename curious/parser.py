from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor

from time import mktime
from datetime import datetime
import parsedatetime

from .grammar import QUERY_PEG


class Parser(object):
  """
  Parses a Wire program into step definitions and connections.
  """

  def __init__(self, code):
    self.object_query = {}
    self.steps = []

    # parsing:
    grammar = Grammar(QUERY_PEG)
    self.__nodes = grammar.parse(code)
    self._translate()

  def _translate(self):
    ast_builder = ASTBuilder()
    query = ast_builder.visit(self.__nodes)
    self.object_query = query[0]
    self.steps = query[1:]


from parsimonious.nodes import NodeVisitor


class ASTBuilder(NodeVisitor):

  def visit_query(self, node, args):
    (obj_query, _1, steps, _2) = args
    if type(steps) == list:
      return [obj_query]+steps[0]
    return [obj_query]

  def visit_object_query(self, node, args):
    (model, filters) = args
    return dict(model=model, method=None, filters=filters)

  def visit_filter_or_id(self, node, f_or_id):
    return f_or_id[0]

  def visit_id_arg(self, node, args):
    (_1, _2, id, _3, _4) = args
    return [dict(method='filter', kwargs=dict(id=id))]

  def visit_steps(self, node, args):
    (step, another_steps) = args
    steps = [step]
    for s in another_steps:
      steps.append(s)
    return steps

  def visit_step(self, node, q):
    return q[0]

  def visit_another_step(self, node, args):
    (_1, step) = args
    return step

  def visit_nj_steps(self, *args):
    return self.visit_steps(*args)

  def visit_another_nj(self, node, args):
    (_1, nj_step) = args
    return nj_step

  def visit_join_query(self, node, args):
    (join, _1, nj_query) = args
    if type(join) == list:
      nj_query['join'] = True
    return nj_query

  def visit_nj_query(self, node, q):
    return q[0]

  def visit_or_query(self, node, args):
    (_1, nj_steps_1, _2, _s1, _3, _s2, _4, nj_steps_2, _5, more_ors) = args
    r = dict(orquery=[nj_steps_1, nj_steps_2], join=False)
    if type(more_ors) == list:
      r['orquery'].extend(more_ors)
    return r

  def visit_another_or(self, node, args):
    (_s1, _1, _s2, _2, nj_steps, _3) = args
    return nj_steps

  def visit_one_query(self, node, args):
    (one_rel, recursion) = args
    if type(recursion) == list:
      one_rel['recursive'] = True
      if recursion[0] == '$':
        one_rel['collect'] = 'terminal'
      elif recursion[0] == '?':
        one_rel['collect'] = 'search'
      elif recursion[0] == '*':
        one_rel['collect'] = 'until'
      else:
        one_rel['collect'] = 'all'
    return one_rel

  def visit_one_rel(self, node, args):
    (model, _1, method, filters) = args
    if type(filters) != list:
      filters = None
    else:
      filters = filters[0]
    return dict(model=model, method=method, filters=filters)

  def visit_sub_query(self, node, args):
    (modifier, _1, q, _2) = args
    join = False
    having = None
    if type(modifier) == list:
      having = modifier[0]
    return dict(subquery=q, having=having, join=join)

  def visit_filters(self, node, args):
    (f, more_filters) = args
    filters = []
    if type(f) == list:
      f[0]['method'] = 'filter'
      filters.append(f[0])
    if type(more_filters) == list:
      filters.extend(more_filters[0])
    return filters

  def visit_name_filters(self, node, args):
    (f, more_filters) = args
    filters = []
    filters.append(f)
    if type(more_filters) == list:
      filters.extend(more_filters)
    return filters

  def visit_name_filter(self, node, args):
    (_1, method, f) = args
    f['method'] = method
    return f

  def visit_filter_group(self, node, args):
    (_1, args, _2) = args
    return args

  def visit_recursion(self, node, _):
    return node.text

  def visit_model(self, node, v):
    return v[0]

  def visit_filter_args(self, node, args):
    if type(args[0]) == dict:
      return {'kwargs': args[0]}
    return {'field': args[0]}

  def visit_filter_kvs(self, node, args):
    (_1, arg, more_args, _2) = args
    d = arg
    for a in more_args:
      d.update(a)
    return d

  def visit_arg(self, node, args):
    (arg_name, _1, equal, _2, value) = args
    d = {}
    d[arg_name] = value
    return d

  def visit_another_arg(self, node, args):
    (_1, comma, _2, arg) = args
    return arg

  def visit_sub_modifier(self, node, _):
    return node.text

  def visit_identifier(self, node, _):
    return node.text

  def visit_id(self, node, _):
    return node.text

  def visit_values(self, node, val):
    return val[0]

  def visit_array_value(self, node, args):
    (br1, _1, value, more_values, _2, br2) = args
    if type(more_values) != list:
      more_values = []
    return [value]+more_values

  def visit_another_val(self, node, args):
    (_1, comma, _2, value) = args
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

  def visit_string(self, node, args):
    (t, s) = args
    if type(t) == list:
      if t[0].text == 't':
        c = parsedatetime.Calendar()
        t = c.parse(s)
        return datetime.fromtimestamp(mktime(t[0]))
      elif t[0].text == 'r':
        return r'%s' % s
    return s

  def visit_q_string(self, node, s):
    return s[0]

  def visit_dq_string(self, node, args):
    (q0, v, q1) = args
    return v.text

  def visit_sq_string(self, node, args):
    (q0, v, q1) = args
    return v.text

  def generic_visit(self, node, visited_children):
    return visited_children or node
