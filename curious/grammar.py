QUERY_PEG = """
# a query starts with an object query and can have many steps
query        = object_query space* sub_query* nl?

# object query: differs from a step in that it must have a filter defining some
# rule to get some objects to seed the query

object_query = model filter_or_id
filter_or_id = id_arg / filters
id_arg       = "(" space* id space* ")"

# single relationship

one_rel      = model "." identifier filters?
filters      = filter_group? name_filters*
name_filters = name_filter name_filter*
name_filter  = "." identifier filter_group
filter_group = "(" filter_args ")"
filter_args  = filter_kvs / identifier
model        = identifier
filter_kvs   = space* arg another_arg* space*
another_arg  = space* "," space* arg
arg          = arg_name space* "=" space* values
arg_name     = identifier
values       = array_value / value
array_value  = bracket_l space* value another_val* space* bracket_r
bracket_l    = "[" / "("
bracket_r    = "]" / ")"
another_val  = space* "," space* value
value        = string / bool / float / int / null

# different ways to recursively search
# *  = searches until looping criteria fails, return all items
# ** = searches exhaustively, return all items matching criteria
# $  = returns last nodes passing criteria
# ?  = searches for and returns first node passing criteria

recursion    = "**" / "*" / "$" / "?"

# a step can be a single relation, multiple relations joined together but
# without a comma. a step can be recursive, and can include another step.

one_relr     = one_rel recursion?
mul_rels     = one_relr another_relr*
another_relr = space* one_relr
rel_group    = "(" steps ")" recursion?
or_rels      = rel_group space* "|" space* rel_group another_or*
another_or   = space* "|" space* rel_group
step         = or_rels / rel_group / mul_rels
steps        = step another_step*
another_step = space* step

join_query   = space* ","? space* steps
lj_modifier  = "+" / "-" / "?"
lj_query     = space* lj_modifier "(" steps ")"

sub_query    = join_query / lj_query / steps

# misc
int          = ~"\\-?[0-9]+"
float        = ~"\\-?[0-9]\\.[0-9]+"
bool         = "True" / "False"
string       = "t"? q_string
q_string     = sq_string / dq_string
dq_string    = "\\\"" ~"[^\\\"]*" "\\\""
sq_string    = "\\\'" ~"[^\\\']*" "\\\'"
null         = "None"
identifier   = ~"[_A-Z][A-Z0-9_]*"i
id           = ~"[A-Z0-9_]+"i
space        = " " / "\\t"
nl           = "\\n"
"""
