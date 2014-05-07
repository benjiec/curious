var app = angular.module('curious', ['ngRoute', 'ngSanitize'])
  .config(['$routeProvider', function($routeProvider) {
    $routeProvider
      .when('/', { template: JST['search'],
                   controller: SearchController})
      .when('/q/:query*', { template: JST['search'],
                            controller: SearchController })
      .otherwise({redirectTo: '/'});
  }]);

app.directive('partial', function($compile) {
  var linker = function(scope, element, attrs) {
    element.html(JST[attrs.template]());
    $compile(element.contents())(scope);
  };
  return {
    link: linker,
    restrict: 'E'
  }
});

app.filter('encodeURIComponent', function() { return window.encodeURIComponent; });
app.filter('encodeURI', function() { return window.encodeURI; });

app.filter('showAttr', function() {
  return function(obj) {
    if (obj && obj.hasOwnProperty('display')) {
      if (obj.display === null || obj.display === undefined) { return ''; }
      return ''+obj.display;
    }
    else { return obj; }
  }
});

app.factory('RecentQueries', function() {
  return [];
});
