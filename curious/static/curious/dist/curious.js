// Each Query object has a main query, as well as an arry of join queries. Each
// join query applies to the results of the previous query or the main query.
// For the time being the main query is treated differently than join queries,
// because we may want to support the concept of a single main query and many
// different arrays of join queries.

function curiousQuery(main_query, join_queries) {
  var q = { main_query: main_query,
            join_queries: join_queries
          };
  return q;
}

// Parses a query from routeParams and returns a curiousQuery object.
//
function curiousParseQueryFromRouteParam(query_param) {
  var q = query_param;
  q = q.split('/');
  return curiousQuery(q[0], q.slice(1));
}

// Parses a query from routeParams and returns a curiousQuery object.
//
function curiousQueryToRouteParam(query) {
  var queries = query.join_queries.slice(0);
  queries.unshift(query.main_query);
  return queries.join('/');
}

// QueryForm: data structure for augmenting an existing query by extending the
// last join, or adding a new join query.

function curiousQueryForm(query, check_query_f, new_query_f, set_form_cb) {
  // Constructor:
  //   query:         in a curiousQuery object
  //   check_query_f: function to call server to check query, takes a query string
  //   set_form_cb:   function to set updated form data structure
  //   new_query_f:   function to call to execute a new query, takes a curiousQuery object

  var form = {
    main_query: query.main_query,
    prev_joins: [],
    last_join: undefined,
    new_join: "",
    query_error: ""
  }

  if (query.join_queries.length > 0) {
    form.prev_joins = query.join_queries.slice(0, query.join_queries.length-1);
    form.last_join = query.join_queries[query.join_queries.length-1];
  }

  function update_form() {
    set_form_cb({
      form: form,
      queryArray: function() { return query_with_all_joins(true); },
      addRelToJoin: add_rel_to_join,
      extendJoin: extend_join,
      addJoinToQuery: add_join_to_query,
      newJoin: new_join
    });
  }

  function query_with_all_joins(return_array) {
    var q = [form.main_query];
    for (var j in form.prev_joins) { q.push(form.prev_joins[j]); }
    if (form.last_join) { q.push(form.last_join); }
    if (form.new_join != '') { q.push(form.new_join); }
    if (return_array && return_array == true) { return q; }
    return q.join(' ');
  }

  // check queries are correct or not. if correct, calls cb with new
  // curiousQuery object.
  //
  function check_queries(cb) {
    var query_to_check = query_with_all_joins();
    check_query_f(query_to_check, function(query, err) {
      if (query !== '') {
        form.query_error = '';
        var queries = query_with_all_joins(true);
        var q = curiousQuery(queries[0], queries.slice(1));
        cb(q);
      }
      else {
        form.query_error = err;
        update_form();
      }
    });
  }

  function add_rel_to_join(model, rel) {
    form.last_join = form.last_join+' '+model+'.'+rel;
    form.new_join = '';
    check_queries(function(q) { new_query_f(q); });
  };

  function extend_join() {
    form.new_join = '';
    check_queries(function(q) { new_query_f(q); });
  };

  function add_join_to_query(model, rel) {
    form.new_join = '';
    // check query first, so we don't push bad queries onto prev_joins
    check_queries(function(q) {
      if (form.last_join) { form.prev_joins.push(form.last_join); }
      form.last_join = model+'.'+rel;
      // don't need to check again, since model+rel is from recommended rels
      var queries = query_with_all_joins(true);
      var q = curiousQuery(queries[0], queries.slice(1));
      new_query_f(q);
    });
  };

  function new_join() {
    // check query first, so we don't push bad queries onto prev_joins
    check_queries(function(q) {
      if (form.last_join) { form.prev_joins.push(form.last_join); }
      form.last_join = form.new_join;
      form.new_join = '';
      // don't need to check again, check_queries already included new_join
      var queries = query_with_all_joins(true);
      var q = curiousQuery(queries[0], queries.slice(1));
      new_query_f(q);
    });
  };

  update_form();
}

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
    var q = curiousParseQueryFromRouteParam($routeParams.query);
    $scope.query = q.main_query;
    $scope.query_submitted = [q];
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

  // query: curiousQuery object
  $scope._new_query = function(query) {
    var query_string = curiousQueryToRouteParam(query);
    var url = '/q/'+encodeURI(query_string);
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
      if (query_string !== '') {
        var url = '/q/'+encodeURI(query_string);
        $location.path(url);
      }
    });
  };

  $scope.newMainQuery = function(query, model, rel) {
    $scope.query = query+' '+model+'.'+rel;
    $scope.submitQuery();
  };
}

var app = angular.module('curious', ['ngRoute'])
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

function curiousJoinTable(join_queries, entries, set_table_cb, get_object_f) {
  // Constructor:
  //   join_queries - array of queries
  //   entries      - 2-dimensional array of objects, each has model and id
  //   set_table_cb - callback to set table data structure, should take a hash
  //   get_object_f - function to fetch an object, should take a model and an id

  var join_queries = join_queries;
  var entries = entries;
  var objects = [];
  var models = [];

  // public variables sent to set_table_cb
  var tbl_queries = [];
  var tbl_attrs = [];
  var tbl_rows = [];
  var tbl_csv = undefined;

  // create a dict of objects, add ptr to object from each cell in entries
  // table. this allows sharing of objects if there are duplicates in query
  // results.
  for (var i=0; i<entries.length; i++) {
    for (var j=0; j<entries[i].length; j++) {
      var entry = entries[i][j];
      var obj_id = entry.model+'.'+entry.id;
      if (objects[obj_id] === undefined) {
        objects[obj_id] = { id: entry.id }
      }
      entry['ptr'] = objects[obj_id];
    }
  }

  // each query has a group of columns, one for each attribute of the query
  // result model. initially, we only show one column per query, just the
  // object ID. as we fetch objects, we expand the table.
  for (var i=0; i<join_queries.length; i++) {
    tbl_queries.push({query: join_queries[i], cols: 1});
  }

  // remeber each query's model
  for (var j=0; j<entries[0].length; j++) {
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
      ptr['id'] = id;
      ptr['__fetched__'] = obj_data;
      for (var a in obj_data) {
        // for each field, we have a value, and a display value that is shown
        // to the user.
        var v = obj_data[a];
        var s = v;
        if (v && v.model && '__str__' in v) {
          s = v['__str__'];
          if (v.id) { s += ' ('+v.id+')'; }
        }
        ptr[a] = {value: v, display: s};
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

'use strict';

function QueryController($scope, $http) {

  function init_query() {
    $scope.search_error = undefined;
    $scope.completed = false;
    $scope.success = false;
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

    var queries = $scope.query.queryArray();
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

  $scope.showCSV = function() {
    $scope.csv = $scope.table.csv();
  }

  curiousQueryForm($scope.query, $scope._check_query, $scope._new_query,
                   function(data) { $scope.query = data; });
  execute();
};
