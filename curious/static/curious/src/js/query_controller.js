'use strict';

function QueryController($scope, $http) {

  function init_query() {
    $scope.completed = false;
    $scope.success = false;
    $scope.search_error = undefined;
    $scope.last_model = undefined;
    $scope.last_model_rels = [];
    $scope.table = undefined;
    $scope.csv = undefined;
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
    var url = $scope.__base_url+'/model/'+model+'/;
    $http.post(url, {ids: ids}).success(function(data) {
      if (data.result) { cb(data.result); }
    });
  }

  function do_query(query_string, cb) {
    var url = $scope.__base_url+'/q/';
    var url = url+'?q='+encodeURIComponent(query_string);
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

    var query = $scope.query;
    do_query(query, function(result, err) {
      $scope.completed = true;
      if (err) {
        $scope.success = false;
        $scope.search_error = err;
      }
      else {
        $scope.success = true;
        if (result.length > 0) {
          $scope.last_model = result[result.length-1].model;
          get_model($scope.last_model, function(result, error) {
            if (result) {
              if (result.relationships) { $scope.last_model_rels = result.relationships; }
            }
          });
          // create join table
          curiousJoinTable(result, function(tbl) { $scope.table = tbl; }, get_objects);
        }
      }
    });
  }

  $scope.showCSV = function() {
    $scope.csv = $scope.table.csv();
  }

  execute();
};
