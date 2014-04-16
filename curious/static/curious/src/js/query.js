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

  function do_query(query, cb) {
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

  function execute() {
    init_query();

    var queries = query_with_all_joins(true);
    curiousJoinQuery(queries, do_query, function(entries, model_name, err) {
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
