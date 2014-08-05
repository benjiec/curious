QUERY_PEG = """
# a query starts with an object query followed by joins
query        = object_query look_ahead* space* chain? join* nl?

# object query: a model and a filter for retrieving some objects of that model
# to start the query.

object_query = model filter_or_id
filter_or_id = id_arg / filters
id_arg       = "(" space* id space* ")"

# the basics: single relationship from a model

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

# a chain is one or more steps. a step is either a relationship or a group of
# steps, with possibility for recursion or look ahead, or an OR of groups. 

chain        = step_rl another_step*
another_step = space+ step_rl
step_rl      = step recursion? look_ahead*
step         = or_step / group / one_rel
group        = "(" chain ")"
or_step      = "(" step_rl space* "|" space* step_rl another_or* ")"
another_or   = space* "|" space* step_rl

# a look-ahead filter is a +/- followed by a chain in parens

look_ahead   = space+ la_modifier "(" chain ")"
la_modifier  = "+" / "-"

# a join is either an inner join or recursive join or a left join

join         = inner_join / recur_join / left_join
inner_join   = space* "," space* chain
recur_join   = space* "," space* "(" chain join* ")" recursion?
left_join    = space* "?" "(" chain ")" recursion?

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
