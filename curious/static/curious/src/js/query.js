'use strict';

function QueryController($scope, $http, $location) {

  function init_query() {
    $scope.search_result = undefined;
    $scope.search_error = undefined;
    $scope.completed = false;
    $scope.success = false;
    $scope.last_model = undefined;
    $scope.last_model_rels = [];
    $scope.table = undefined;
  }

  function get_model(model, cb) {
    var url = $scope.__base_url+'/models/'+model+'/';
    $http.get(url).success(function(data) {
      if (data.result) { cb(data.result, undefined); }
      else { cb(undefined, "Cannot retrieve model information from server"); }
    })
    .error(function(data, status, headers, config) {
      if (data.error) { cb(undefined, data.error.message); }
      else { cb(undefined, "Unspecified error from server"); }
    });
  }

  function get_object(model, id, cb) {
    var url = $scope.__base_url+'/objects/'+model+'/'+id+'/';
    $http.get(url).success(function(data) {
      if (data.result) { cb(data.result); }
    });
  }

  function make_query(query, cb) {
    var url = $scope.__base_url+'/q/';
    var url = url+'?q='+encodeURIComponent(query);
    $http.get(url)
      .success(function(data) {
        if (data.result) { cb(data.result, undefined); }
        else { cb(undefined, "Did not receive results from server"); }
      })
      .error(function(data, status, headers, config) {
        if (data.error) { cb(undefined, data.error.message); }
        else { cb(undefined, "Unspecified error from server"); }
      });
  }

  // for each entry in entries array, construct a new query using the last
  // object and new_query. this essentially does a join client side. returns
  // array of new queries and error.
  //
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
  //
  function join(entries, last_model_name, queries, cb) {

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
          for (var n in result.ids) {
            var new_entry = entry.slice(0);
            new_entry.push({id: result.ids[n], model: result.model});
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
        make_query(query.query, function(result, err) { // on completion of each query
          query.completed = true;
          if (result) { query.result = result; }
          else { query.error = err; }
          if (_completed()) { _expand_entries_and_join(); }
        });
      }
      mk_query(i);
    }
  }

  function execute() {
    init_query();

    var queries = query_with_all_joins(true);
    var entries = [[]];

    join(entries, undefined, queries, function(entries, model_name, err) {
      $scope.completed = true;
      if (err) {
        $scope.success = false;
        $scope.search_error = err;
      }
      else {
        $scope.success = true;
        if (entries.length > 0) {
          // fetch information about the model of the last query, so we can
          // list recommended relationships.
          $scope.last_model = model_name;
          get_model(model_name, function(result, error) {
            if (result) {
              if (result.relationships) { $scope.last_model_rels = result.relationships; }
            }
          });
          // create join table
          curiousJoinTable(queries, entries, function(tbl) { $scope.table = tbl; }, get_object);
        }
      }
    });
  }

  function query_with_all_joins(array) {
    var q = [$scope.q_j.main_query];
    for (var j in $scope.q_j.prev_joins) { q.push($scope.q_j.prev_joins[j]); }
    if ($scope.q_j.last_join) { q.push($scope.q_j.last_join); }
    if ($scope.q_j.new_join != '') { q.push($scope.q_j.new_join); }
    if (array && array == true) { return q; }
    return q.join(' ');
  }

  function check_queries(cb) {
    var query_to_check = query_with_all_joins();
    $scope._checkQuery(query_to_check, function(query, err) {
      if (query !== '') {
        $scope.query_error = '';
        var queries = query_with_all_joins(true);
        cb(queries);
      }
      else { $scope.query_error = err; }
    });
  }

  function new_query(queries) {
    var q = queries.join('/');
    var url = '/q/'+encodeURI(q);
    $location.path(url);
  }

  $scope.addRelToJoin = function(model, rel) {
    $scope.q_j.last_join = $scope.q_j.last_join+' '+model+'.'+rel;
    $scope.q_j.new_join = '';
    check_queries(function(queries) { new_query(queries); });
  };

  $scope.extendJoin = function() {
    $scope.q_j.new_join = '';
    check_queries(function(queries) { new_query(queries); });
  };

  $scope.addJoinToQuery = function(model, rel) {
    $scope.q_j.new_join = '';
    // check query first, so we don't push bad queries onto prev_joins
    check_queries(function(queries) {
      if ($scope.q_j.last_join) { $scope.q_j.prev_joins.push($scope.q_j.last_join); }
      $scope.q_j.last_join = model+'.'+rel;
      // don't need to check again, since model+rel is from recommended rels
      queries = query_with_all_joins(true);
      new_query(queries);
    });
  };

  $scope.newJoin = function() {
    // check query first, so we don't push bad queries onto prev_joins
    check_queries(function(queries) {
      if ($scope.q_j.last_join) { $scope.q_j.prev_joins.push($scope.q_j.last_join); }
      $scope.q_j.last_join = $scope.q_j.new_join;
      $scope.q_j.new_join = '';
      // don't need to check again, check_queries already included new_join
      queries = query_with_all_joins(true);
      new_query(queries);
    });
  };


  $scope.q_j = { main_query: $scope.query.query,
                 prev_joins: [],
                 last_join: undefined,
                 new_join: "" }
  $scope.query_error = '';

  if ($scope.query.joins.length > 0) {
    $scope.q_j.prev_joins = $scope.query.joins.slice(0, $scope.query.joins.length-1);
    $scope.q_j.last_join = $scope.query.joins[$scope.query.joins.length-1];
  }

  init_query();
  execute();
};
