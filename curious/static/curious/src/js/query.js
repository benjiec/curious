// Each Query object has a main query, as well as an arry of join queries. Each
// join query applies to the results of the previous query or the main query.
// For the time being the main query is treated differently than join queries,
// because we may want to support the concept of a single main query and many
// different arrays of join queries.

function curiousQuery(main_query, join_queries) {
  var q = { main_query: main_query,
            join_queries: join_queries
          };
  return q;
}

// Parses a query from routeParams and returns a curiousQuery object.
//
function curiousParseQueryFromRouteParam(query_param) {
  var q = query_param;
  q = q.split('/');
  return curiousQuery(q[0], q.slice(1));
}

// Parses a query from routeParams and returns a curiousQuery object.
//
function curiousQueryToRouteParam(query) {
  var queries = query.join_queries.slice(0);
  queries.unshift(query.main_query);
  return queries.join('/');
}

// QueryForm: data structure for augmenting an existing query by extending the
// last join, or adding a new join query.

function curiousQueryForm(query, check_query_f, new_query_f, set_form_cb) {
  // Constructor:
  //   query:         in a curiousQuery object
  //   check_query_f: function to call server to check query, takes a query string
  //   set_form_cb:   function to set updated form data structure
  //   new_query_f:   function to call to execute a new query, takes a curiousQuery object

  var form = {
    main_query: query.main_query,
    prev_joins: [],
    last_join: undefined,
    new_join: "",
    query_error: ""
  }

  if (query.join_queries.length > 0) {
    form.prev_joins = query.join_queries.slice(0, query.join_queries.length-1);
    form.last_join = query.join_queries[query.join_queries.length-1];
  }

  function update_form() {
    set_form_cb({
      form: form,
      queryArray: function() { return query_with_all_joins(true); },
      addRelToJoin: add_rel_to_join,
      extendJoin: extend_join,
      addJoinToQuery: add_join_to_query,
      newJoin: new_join
    });
  }

  function query_with_all_joins(return_array) {
    var q = [form.main_query];
    for (var j in form.prev_joins) { q.push(form.prev_joins[j]); }
    if (form.last_join) { q.push(form.last_join); }
    if (form.new_join != '') { q.push(form.new_join); }
    if (return_array && return_array == true) { return q; }
    return q.join(' ');
  }

  // check queries are correct or not. if correct, calls cb with new
  // curiousQuery object.
  //
  function check_queries(cb) {
    var query_to_check = query_with_all_joins();
    check_query_f(query_to_check, function(query, err) {
      if (query !== '') {
        form.query_error = '';
        var queries = query_with_all_joins(true);
        var q = curiousQuery(queries[0], queries.slice(1));
        cb(q);
      }
      else {
        form.query_error = err;
        update_form();
      }
    });
  }

  function add_rel_to_join(model, rel) {
    form.last_join = form.last_join+' '+model+'.'+rel;
    form.new_join = '';
    check_queries(function(q) { new_query_f(q); });
  };

  function extend_join() {
    form.new_join = '';
    check_queries(function(q) { new_query_f(q); });
  };

  function add_join_to_query(model, rel) {
    form.new_join = '';
    // check query first, so we don't push bad queries onto prev_joins
    check_queries(function(q) {
      if (form.last_join) { form.prev_joins.push(form.last_join); }
      form.last_join = model+'.'+rel;
      // don't need to check again, since model+rel is from recommended rels
      var queries = query_with_all_joins(true);
      var q = curiousQuery(queries[0], queries.slice(1));
      new_query_f(q);
    });
  };

  function new_join() {
    // check query first, so we don't push bad queries onto prev_joins
    check_queries(function(q) {
      if (form.last_join) { form.prev_joins.push(form.last_join); }
      form.last_join = form.new_join;
      form.new_join = '';
      // don't need to check again, check_queries already included new_join
      var queries = query_with_all_joins(true);
      var q = curiousQuery(queries[0], queries.slice(1));
      new_query_f(q);
    });
  };

  update_form();
}
