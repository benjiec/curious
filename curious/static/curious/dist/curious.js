var app = angular.module('curious', ['ngRoute', 'ngSanitize'])
  .config(['$routeProvider', function($routeProvider) {
    $routeProvider
      .when('/', {template: JST['search'],
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
    if (obj && obj.hasOwnProperty('display')) { return obj.display; }
    else { return obj; }
  }
});

app.factory('RecentQueries', function() {
  return [];
});

// A JoinTable manages objects returned by a set of join queries. JoinTable
// exposes a data structure that angular template can easily use to display the
// objects and their attributes.

function curiousJoinTable(results, set_table_cb, get_object_f) {
  // Constructor:
  //   results      - array of search results, each result has a model and a
  //                  list of object output input tuples
  //   set_table_cb - callback to set table data structure, should take a hash
  //   get_object_f - function to fetch an object, should take a model and an id

  var entries = [];
  var objects = [];
  var models = [];

  // public variables sent to set_table_cb
  var tbl_queries = [];
  var tbl_attrs = [];
  var tbl_rows = [];
  var tbl_csv = undefined;

  // from results, construct entries table - joining results together

  // for each result, build a dict indexed by object id
  for (var i=0; i<results.length; i++) {
    results[i].map = {}
    for (var j=0; j<results[i].objects.length; j++) {
      var obj = results[i].objects[j];
      if (results[i].map[obj[0]] === undefined) { results[i].map[obj[0]] = []; }
      results[i].map[obj[0]].push(obj);
    }
  }

  function build_obj(col, res_obj) {
    return { model: results[col].model,
             id: res_obj[0],
             url: res_obj[1],
             from: res_obj[2] };
  }

  var entries = [];
  var last_column = results[results.length-1];
  for (var i=0; i<last_column.objects.length; i++) {
    entries.push([build_obj(results.length-1, last_column.objects[i])]);
  }

  for (var col=results.length-2; col>=0; col--) {
    var new_entries = [];
    for (var i=0; i<entries.length; i++) {
      var row = entries[i];
      var last_from = row[0].from;
      // index last_from in current column
      var objs = results[col].map[last_from];
      for (var j=0; j<objs.length; j++) {
        var new_row = row.slice(0);
        new_row.unshift(build_obj(col, objs[j]));
        new_entries.push(new_row);
      }
    }
    entries = new_entries;
  }

  // sort by first column
  entries.sort(function(a, b) { return a[0].id-b[0].id; });

  // create a dict of objects, add ptr to object from each cell in entries
  // table. this allows sharing of objects if there are duplicates in query
  // results.
  for (var i=0; i<entries.length; i++) {
    for (var j=0; j<entries[i].length; j++) {
      var entry = entries[i][j];
      var obj_id = entry.model+'.'+entry.id;
      if (objects[obj_id] === undefined) {
        var id_str = ''+entry.id;
        if (entry.url) { id_str = '<a href="'+entry.url+'">'+entry.id+'</a>'; }
        objects[obj_id] = {id: {value: entry.id, display: id_str }};
      }
      entry['ptr'] = objects[obj_id];
    }
  }

  // remeber each query's model
  for (var j=0; j<entries[0].length; j++) {
    tbl_queries.push({model: entries[0][j].model, cols: 1});
    models.push({model: entries[0][j].model,
                 attrs: ['id'],
                 loaded: false});
  }

  // fetching object from server or cache
  function get_object(model, id, cb) {
    var obj_id = model+'.'+id;
    if (obj_id in objects && objects[obj_id]['__fetched__']) {
      cb(objects[obj_id]['__fetched__']);
      return;
    }

    get_object_f(model, id, function(obj_data) {
      var ptr = objects[obj_id];
      ptr['__fetched__'] = obj_data;
      for (var a in obj_data) {
        // already has id field with link, don't overwrite that
        if (a !== 'id') {
          // for each field, we have a value, and a display value that is shown
          // to the user.
          var v = obj_data[a];
          var s = v;
          if (v && v.model) {
            if ('__str__' in v) {
              s = v['__str__'];
              if (v.id) { s += ' ('+v.id+')'; }
            }
            if ('url' in v) { s = '<a href="'+v.url+'">'+s+'</a>'; }
          }
          ptr[a] = {value: v, display: s};
        }
      }
      // console.log(ptr);
      if (cb) { cb(obj_data); }
    });
  }

  function csv() {
    if (tbl_rows.length == 0) { return ""; }
    var csv_rows = []

    var row0 = tbl_rows[0];
    var header = [];
    for (var i=0; i<tbl_attrs.length; i++) {
      var model = row0[i].model;
      header.push(model+'.'+tbl_attrs[i]);
    }
    csv_rows.push(header.join(','));

    for (var i=0; i<tbl_rows.length; i++) {
      var row = [];
      for (var j=0; j<tbl_rows[i].length; j++) {
        var entry = tbl_rows[i][j];
        if (entry) {
          var obj = entry.ptr;
          if (obj) {
            var v = obj[tbl_attrs[j]];
            if (v.display) { v = v.display; }
            if (v) {
              v = ''+v;
              // dumb escape logic for csv value - basically gets rid of space and quotes
              v = v.replace("\n", " ");
              v = v.replace("\t", " ");
              v = v.replace("\"", "");
              v = v.replace("\'", "");
              v = "\""+v+"\"";
            }
            row.push(v);
          }
          else {
            if (tbl_attrs[j] == 'id') { row.push(entry.id); }
            else { row.push(''); }
          }
        }
        else {
          if (tbl_attrs[j] == 'id') { row.push(entry.id); }
          else { row.push(''); }
        }
      }
      csv_rows.push(row.join(','));
    }

    return csv_rows.join('\n');
  }

  // update table data structure after a model's attributes list has changed.
  // the attributes list can change if user wants to show or hide a model's
  // attributes.
  function update_table() {
    tbl_attrs = [];
    var attr_model_idx = [];
    for (var i=0; i<models.length; i++) {
      for (var j=0; j<models[i].attrs.length; j++) {
        tbl_attrs.push(models[i].attrs[j]);
        attr_model_idx.push(i);
      }
    }
    // console.log(tbl_attrs);

    tbl_rows = [];
    for (var i=0; i<entries.length; i++) {
      var row = [];
      for (var j=0; j<tbl_attrs.length; j++) {
        var k = attr_model_idx[j];
        row.push(entries[i][k]);
      }
      tbl_rows.push(row);
    }
    // console.log(tbl_rows);

    if (tbl_csv) { tbl_csv = csv(); }
    update_controller();
  }

  function update_controller() {
    // tell angular to re-render
    set_table_cb({
      toggle: toggle,
      showCSV: showCSV,
      csv: tbl_csv,
      queries: tbl_queries,
      attrs: tbl_attrs,
      rows: tbl_rows
    });
  }

  // after fetching the first object from a query's results, update the query
  // model attributes list.
  function update_model_attrs(query_idx, object) {
    if (models[query_idx].attrs.length == 1) {
      var attrs = [];
      for (var a in object) { if (a !== 'id') { attrs.push(a); } }
      attrs.sort();
      attrs.unshift('id');
      models[query_idx].attrs = attrs;
      tbl_queries[query_idx].cols = attrs.length;
      update_table();
    }
  }

  // show attributes for a query's objects
  function show_object_attrs(query_idx) {
    if (models[query_idx].loaded == true) {
      // already loaded, just use one fetched object to expand the attributes
      // list.
      obj = entries[0][query_idx];
      get_object(obj.model, obj.id, function(obj_data) {
        update_model_attrs(query_idx, obj_data);
      });
      return;
    }

    // fetch every object from server
    for (var i=0; i<entries.length; i++) {
      var obj = entries[i][query_idx];
      // console.log('fetch '+obj.model+'.'+obj.id);
      get_object(obj.model, obj.id, function(obj_data) {
        update_model_attrs(query_idx, obj_data);
      });
    }
    models[query_idx].loaded = true;
  }

  // hide attributes for a query's objects
  function hide_object_attrs(query_idx) {
    models[query_idx].attrs = ['id'];
    tbl_queries[query_idx].cols = 1;
    update_table();
  }

  function toggle(query_idx) {
    if (models[query_idx].attrs.length == 1) { show_object_attrs(query_idx); }
    else { hide_object_attrs(query_idx); }
  }

  function showCSV() {
    tbl_csv = csv();
    update_controller();
  }

  update_table(); // initialize table

  // by default, fetch objects from last query if table is not too big
  if (entries.length < 200) { show_object_attrs(entries[0].length-1); }
}

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
          curiousJoinTable(result, function(tbl) { $scope.table = tbl; }, get_object);
        }
      }
    });
  }

  $scope.showCSV = function() {
    $scope.csv = $scope.table.csv();
  }

  execute();
};

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

  $scope.newQuery = function(query, model, rel) {
    $scope.query = query+' '+model+'.'+rel;
    $scope.submitQuery();
  };
}
