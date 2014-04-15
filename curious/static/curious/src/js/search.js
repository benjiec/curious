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
    var q = $routeParams.query;
    q = q.split('/');
    $scope.query = q[0];
    $scope.query_submitted = [{ query: $scope.query, joins: q.slice(1) }];
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

  $scope._checkQuery = function (query, cb) {
    var url = $scope.__base_url+'/q/';
    var url = url+'?c=1&q='+encodeURIComponent(query);
    $http.get(url)
      .success(function(data) { cb(data.result.query, ''); })
      .error(function(data, status, headers, config) {
        var err = '';
        if (data.error) { err = data.error.message; }
        else { err = 'Unspecified error'; }
        cb('', err);
      });
  };

  $scope.checkQuery = function(cb) {
    $scope._checkQuery($scope.query, function(query, err) {
      $scope.query_error = err;
      $scope.query_accepted = query;
      if (cb !== undefined) { cb(query, err); }
    });
  };

  $scope.submitQuery = function () {
    $scope.checkQuery(function(query, err) {
      if (query !== '') {
        var url = '/q/'+encodeURI(query);
        $location.path(url);
      }
    });
  };

  $scope.addRelToQuery = function(query, model, rel) {
    $scope.query = query+' '+model+'.'+rel;
    $scope.submitQuery();
  };
}
