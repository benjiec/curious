'use strict';

function SearchController($scope, $routeParams, $http, $timeout, $location, RecentQueries) {
  $scope.__base_url = '/curious';

  // SearchController object cache 
  $scope._object_cache = {};

  $scope.query = '';
  $scope.query_error = '';
  $scope.query_accepted = '';

  $scope.delayPromise = undefined;
  $scope.recent_queries = RecentQueries;

  $scope.query_submitted = [];

  if ($routeParams && $routeParams.query) {
    $scope.query = $routeParams.query;
    $scope.query_submitted = [{query: $scope.query, reload: false}];
    var i = $scope.recent_queries.indexOf($routeParams.query);
    if (i < 0) { $scope.recent_queries.unshift($routeParams.query); }
  }

  var url = $scope.__base_url+'/models/';
  $http.get(url).success(function(data) {
    if (data.result) {
      var models = data.result;
      var by_module = {};
      for (var i=0; i<models.length; i++) {
        var model = models[i];
        if (model.indexOf("__") >= 0) {
          var tokens = model.split("__");
          if (!by_module[tokens[0]])
            by_module[tokens[0]] = [];
          by_module[tokens[0]].push(tokens.slice(1).join("__"));
        }
        else {
          if (!by_module[""])
            by_module[""] = [];
          by_module[""].push(model);
        }
      }
      var modules = [];
      for (var k in by_module) {
        by_module[k].sort();
        modules.push({ module: k, models: by_module[k] });
      }
      $scope.modules = modules;
    }
  });

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
    // convert newlines into spaces
    query_string = query_string.replace(/\n/g, " ");
    var url = $scope.__base_url+'/q/';
    $http.post(url, {c: 1, app: 'curious-ui', q: query_string})
      .success(function(data) { cb(data.result.query, ''); })
      .error(function(data, status, headers, config) {
        var err = '';
        if (data.error) { err = data.error.message; }
        else { err = 'Unspecified error'; }
        cb('', err);
      });
  };

  $scope._new_query = function(query, reload) {
    var url = '/q/'+encodeURI(query);
    $location.path(url);
    $scope.query_submitted = [{query: $scope.query, reload: reload}];
  }

  $scope.checkQuery = function(cb) {
    if ($scope.query != '') {
      $scope._check_query($scope.query, function(query_string, err) {
        $scope.query_error = err;
        $scope.query_accepted = query_string;
        if (cb !== undefined) { cb(query_string, err); }
      });
    }
  };

  $scope.submitQuery = function(reload) {
    if (reload === undefined) { reload = false; }
    $scope.checkQuery(function(query_string, err) {
      if (query_string !== '') { $scope._new_query(query_string, reload); }
    });
  };

  $scope.refreshQuery = function () {
    $scope.reload = true;
  };

  $scope.extendQuery = function(model, rel) {
    $scope.query = $scope.query+' '+model+'.'+rel;
    $scope.submitQuery();
  };
}
