'use strict';

function QueryController($scope, $http) {

  function init_query() {
    $scope.completed = false;
    $scope.success = false;
    $scope.search_error = undefined;
    $scope.last_model = undefined;
    $scope.last_model_rels = [];
    $scope.computed_on = undefined;
    $scope.computed_since = undefined;
    $scope.table = undefined;
    $scope.csv = false;
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

  function get_objects(model, ids, cb) {
    var url = $scope.__base_url+'/models/'+model+'/';
    $http.post(url, {app: 'curious-ui', r: 1, ids: ids}).success(function(data) {
      if (data.result) { cb(data.result); }
    });
  }

  function do_query(query_string, reload, cb) {
    var url = $scope.__base_url+'/q/';
    var params = {app: 'curious-ui', q: query_string};
    if (reload) { params['r'] = 1; }
    $http.post(url, params)
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

    var query = $scope.query;
    // convert newlines into spaces
    query = query.replace(/\n/g, " ");

    do_query(query, $scope.query_info.reload, function(res, err) {
      $scope.completed = true;
      if (err) {
        $scope.success = false;
        $scope.search_error = err;
      }
      else {
        $scope.success = true;
        if (res.last_model) { $scope.last_model = res.last_model; }
        if (res.computed_on) { $scope.computed_on = res.computed_on; }
        if (res.computed_since) { $scope.computed_since = res.computed_since; }
        if (res.results.length > 0) {
          if ($scope.last_model) {
            get_model($scope.last_model, function(res, error) {
              if (res) { if (res.relationships) { $scope.last_model_rels = res.relationships; } }
            });
          }
          // create join table
          curiousJoinTable(res.results,
                           function(tbl) { $scope.table = tbl; },
                           function() { return $scope.$parent._object_cache; },
                           get_objects);
        }
      }
    });
  }

  $scope.toggleCSV = function() {
    if ($scope.csv) { $scope.csv = false; }
    else {
      if (!$scope.table.csv) { $scope.table.showCSV(); }
      $scope.csv = true;
    }
  };

  $scope.query = $scope.query_info.query;
  execute();
};
