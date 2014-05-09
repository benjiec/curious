QUERY_PEG = """
query        = object_query space* steps? nl?
object_query = model filter_or_id
filter_or_id = id_arg / filters
id_arg       = "(" space* id space* ")"
steps        = step another_step*
another_step = space* step
step         = one_query / sub_query
sub_query    = modifier? "(" steps ")"
modifier     = "+" / "-"
one_query    = join? space* one_rel recursion?
join         = ","
recursion    = "*" "*"?
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
int          = ~"\\-?[0-9]+"
float        = ~"\\-?[0-9]\\.[0-9]+"
bool         = "True" / "False"
string       = sq_string / dq_string
dq_string    = "\\\"" ~"[^\\\"]*" "\\\""
sq_string    = "\\\'" ~"[^\\\']*" "\\\'"
null         = "None"
identifier   = ~"[_A-Z][A-Z0-9_]*"i
id           = ~"[A-Z0-9_]+"i
space        = " " / "\\t"
nl           = "\\n"
"""
