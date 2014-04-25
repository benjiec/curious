from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor
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

  def visit_query(self, node, (obj_query, _1, steps, _2)):
    if type(steps) == list:
      return [obj_query]+steps[0]
    return [obj_query]

  def visit_object_query(self, node, (model, filters)):
    return dict(model=model, method=None, filters=filters)

  def visit_filter_or_id(self, node, f_or_id):
    return f_or_id[0]

  def visit_id_arg(self, node, (_1, _2, id, _3, _4)):
    return {'__id__': id}

  def visit_steps(self, node, (step, another_steps)):
    steps = [step]
    for s in another_steps:
      steps.append(s)
    return steps

  def visit_another_step(self, node, (_1, step)):
    return step

  def visit_step(self, node, q):
    return q[0]

  def visit_sub_query(self, node, (modifier, _1, q, _2)):
    if modifier == '-':
      w = False
    else:
      w = True
    return dict(subquery=q, having=w)

  def visit_one_query(self, node, (join, _1, one_rel, recursion)):
    if type(join) == list:
      one_rel['join'] = True
    if type(recursion) == list:
      one_rel['recursive'] = True
      if recursion[0] is True:
        one_rel['collect'] = 'terminal'
      else:
        one_rel['collect'] = 'intermediate'
    return one_rel

  def visit_one_rel(self, node, (model, _1, method, rel_filter)):
    if type(rel_filter) != list:
      rel_filter = None
    else:
      rel_filter = rel_filter[0]
    return dict(model=model, method=method, filters=rel_filter)

  def visit_rel_filter(self, node, (ex, _1, filters, _2)):
    if type(ex) == list and ex[0].text != '':
      filters['__exclude__'] = True
    return filters

  def visit_recursion(self, node, (star, double_star)):
    """Returns True if collecting terminal nodes, False if collecting intermediate nodes"""
    if type(double_star) == list and double_star[0].text == '*':
      return True
    return False

  def visit_model(self, node, v):
    return v[0]

  def visit_filters(self, node, (_1, arg, more_args, _2)):
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

  def visit_modifier(self, node, _):
    return node.text

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

  def visit_string(self, node, s):
    return s[0]

  def visit_dq_string(self, node, (q0, v, q1)):
    return v.text

  def visit_sq_string(self, node, (q0, v, q1)):
    return v.text

  def generic_visit(self, node, visited_children):
    return visited_children or node
