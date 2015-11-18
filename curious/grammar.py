QUERY_PEG = """
# a query starts with an object query and can have many steps

query        = object_query space* steps? nl?

# object query: differs from a step in that it must have a filter defining some
# rule to get some objects to seed the query

object_query = model filter_or_id
filter_or_id = id_arg / filters
id_arg       = "(" space* id space* ")"

# different ways to recursively search
# *  = searches until looping criteria fails, return all items
# ** = searches exhaustively, return all items matching criteria
# $  = returns last nodes passing criteria
# ?  = searches for and returns first node passing criteria

recursion    = "**" / "*" / "$" / "?"

# steps for query can be a single step, possibly joining with previous step, or
# a subquery. a single step can be a single relationship, or an OR.

step         = join_query / sub_query
join         = ","
join_query   = join? space* nj_query
nj_query     = one_query / or_query

steps        = step another_step*
another_step = space* step
nj_steps     = nj_query another_nj*
another_nj   = space* nj_query

sub_modifier = "+" / "-" / "?"
# cannot do joins in sub queries
sub_query    = sub_modifier? "(" nj_steps ")"

one_query    = one_rel recursion?
# cannot do joins in or queries
or_query     = "(" nj_steps ")" space* "|" space* "(" nj_steps ")" another_or*
another_or   = space* "|" space* "(" nj_steps ")"

# single relationship

one_rel      = model "." identifier filters?
filters      = filter_group? name_filters*
name_filters = name_filter name_filter*
name_filter  = "." identifier filter_group
filter_group = "(" filter_args ")"
filter_args  = filter_kvs / identifier / int
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

# misc
int          = ~"\\-?[0-9]+"
float        = ~"\\-?[0-9]\\.[0-9]+"
bool         = "True" / "False"
string       = ~"[tr]"? q_string
q_string     = sq_string / dq_string
dq_string    = "\\\"" ~"[^\\\"]*" "\\\""
sq_string    = "\\\'" ~"[^\\\']*" "\\\'"
null         = "None"
identifier   = ~"[_A-Z][A-Z0-9_]*"i
id           = ~"[A-Z0-9_]+"i
space        = " " / "\\t"
nl           = "\\n"
"""
