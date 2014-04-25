'use strict';

function SearchController($scope, $routeParams, $http, $timeout, $location, RecentQueries) {
  $scope.__base_url = '/curious';

  $scope.query = '';
  $scope.query_error = '';
  $scope.query_accepted = '';

  $scope.delayPromise = undefined;
  $scope.recent_queries = RecentQueries;

  $scope.query_submitted = [];

  if ($routeParams && $routeParams.query) {
    $scope.query = $routeParams.query;
    $scope.query_submitted = [$scope.query];
    var i = $scope.recent_queries.indexOf($routeParams.query);
    if (i < 0) { $scope.recent_queries.unshift($routeParams.query); }
  }

  $scope.delayCheckQuery = function() {
    if ($scope.delayPromise !== undefined) {
      $timeout.cancel($scope.delayPromise);
      $scope.delayPromise = undefined;
    }
    $scope.delayPromise = $timeout(function() {
      $scope.checkQuery();
      $scope.delayPromise = undefined;
    }, 1000);
  };

  $scope._check_query = function(query_string, cb) {
    var url = $scope.__base_url+'/q/';
    var url = url+'?c=1&q='+encodeURIComponent(query_string);
    $http.get(url)
      .success(function(data) { cb(data.result.query, ''); })
      .error(function(data, status, headers, config) {
        var err = '';
        if (data.error) { err = data.error.message; }
        else { err = 'Unspecified error'; }
        cb('', err);
      });
  };

  $scope._new_query = function(query) {
    var url = '/q/'+encodeURI(query);
    $location.path(url);
  }

  $scope.checkQuery = function(cb) {
    $scope._check_query($scope.query, function(query_string, err) {
      $scope.query_error = err;
      $scope.query_accepted = query_string;
      if (cb !== undefined) { cb(query_string, err); }
    });
  };

  $scope.submitQuery = function () {
    $scope.checkQuery(function(query_string, err) {
      if (query_string !== '') { $scope._new_query(query_string); }
    });
  };

  $scope.extendQuery = function(model, rel) {
    $scope.query = $scope.query+' '+model+'.'+rel;
    $scope.submitQuery();
  };
}
