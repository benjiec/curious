// JoinQuery takes a list of queries, call first one, then recursively call
// each subsequent query on prev query's results.

function curiousJoinQuery(queries, do_query_f, cb) {

  // for each entry in entries array, construct a new query using the last
  // object and new_query. this essentially does a join client side. returns
  // array of new queries and error.
  function get_join_queries(entries, last_model_name, new_query) {
    var new_queries = [];
    for (var i=0; i<entries.length; i++) {
      var entry = entries[i];
      // put together a query, if there is a prev object in entry, use it as
      // the prefix to the query.
      if (entry.length > 0) {
        // get last object
        var last = entry[entry.length-1];
        if (last.id) {
          new_queries.push(last_model_name+'('+last.id+') '+new_query);
        }
        else {
          return [undefined, "No ID field for object of type "+last_model_name];
        }
      }
      else { new_queries.push(new_query); }
    }
    return [new_queries, undefined];
  }

  // entries should be an array, each array member itself is an array of
  // objects. join entries with remaining queries. call cb with final entries,
  // last model name, and error.
  function join(entries, last_model_name, queries) {

    if (queries.length == 0) { cb(entries, last_model_name, undefined); return; }
    var query = queries[0];
    queries = queries.slice(1);

    var qres = get_join_queries(entries, last_model_name, query);
    if (qres[1]) { cb(undefined, undefined, qres[1]); }
    var new_queries = qres[0];

    for (var i=0; i<new_queries.length; i++) {
      new_queries[i] = { query: new_queries[i], completed: false, result: undefined, error: undefined };
    }

    // check if all queries have completed
    function _completed() {
      for (var i=0; i<new_queries.length; i++) {
        if (new_queries[i].completed == false) { return false; }
      }
      return true;
    }

    // check if any of the queries have failed
    function _err() {
      for (var i=0; i<new_queries.length; i++) {
        if (new_queries[i].completed == true && new_queries[i].error) { return new_queries[i].error; }
      }
      return undefined;
    }

    // when all queries have completed, run this
    function _expand_entries_and_join() {
      var err = _err();
      if (err) { cb(undefined, undefined, err); }
      else {
        // expand entries - this is the join step
        var new_entries = [];
        var next_model_name = undefined;
        for (var i=0; i<entries.length; i++) {
          var entry = entries[i];
          var result = new_queries[i].result;
          if (result.model) { next_model_name = result.model; }
          for (var n in result.objects) {
            var new_entry = entry.slice(0);
            new_entry.push({id: result.objects[n][0],
                            model: result.model,
                            url: result.objects[n][1]});
            new_entries.push(new_entry);
          }
        }
        join(new_entries, next_model_name, queries, cb);
      }
    }

    // execute each new query in new_queries, extend corresponding entry in
    // entries
    for (var i=0; i<new_queries.length; i++) {
      var mk_query = function(i) { // use function to create closure with separate copy of query
        var query = new_queries[i];
        do_query_f(query.query, function(result, err) { // on completion of each query
          query.completed = true;
          if (result) { query.result = result; }
          else { query.error = err; }
          if (_completed()) { _expand_entries_and_join(); }
        });
      }
      mk_query(i);
    }
  }

  join([[]], undefined, queries);
}
