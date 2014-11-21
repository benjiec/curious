// A JoinTable manages objects returned by a query. JoinTable exposes a data
// structure that angular template can easily use to display the objects and
// their attributes.

function curiousJoinTable(query_results_raw, set_table_cb, object_cache_f, get_objects_f) {
  // Constructor:
  //   query_results  - array of search results, each result has a model and a
  //                    list of object output input tuples
  //   set_table_cb   - callback to set table data structure, should take a hash
  //   object_cache_f - function to call to get object cache
  //   get_objects_f  - function to fetch objects in batch, should take a model
  //                    and an ids list

  var GET_BATCH = 300;  // how many objects to fetch from server at a time
  var DEFAULT_PAGE_SIZE = 100;
  var PARTIAL_FETCH = 3000; // auto fetch all when total is below this threshold

  var entries;
  var models;
  var left_join_mode;
  var tbl_attrs;
  var tbl_rows;
  var tbl_view;
  var tbl_csv;
  var tbl_controls;
  var partial_fetch;
  var pourover_collection;
  var outstanding_fetches;

  // get reference to object cache once
  var object_cache = object_cache_f();

  // get rid of empty columns
  var query_results = [];
  for (var i=0; i<query_results_raw.length; i++) {
    if (query_results_raw[i].model && query_results_raw[i].objects.length > 0) {
      query_results.push(query_results_raw[i]);
      // update join index of later columns that joins with this column
      for (var j=i+1; j<query_results_raw.length; j++) {
        if (query_results_raw[j].join_index === i) {
          query_results_raw[j].join_index = query_results.length-1;
        }
      }
    }
  }

  function process_results(lj) {
    left_join_mode = lj;
    entries = [];
    models = [];
    tbl_attrs = [];
    tbl_rows = [];
    tbl_view = undefined;
    tbl_csv = undefined;
    tbl_controls = {};
    partial_fetch = undefined;
    pourover_collection = undefined;
    outstanding_fetches = 0;

    // from results, construct entries table - joining results together

    // for each result, build dict indexed by from id
    for (var i=0; i<query_results.length; i++) {
      query_results[i].map = {}
      for (var j=0; j<query_results[i].objects.length; j++) {
        var obj = query_results[i].objects[j];
        if (query_results[i].map[obj[1]] === undefined) { query_results[i].map[obj[1]] = []; }
        query_results[i].map[obj[1]].push(obj);
      }
    }

    function build_obj(col, res_obj) {
      return { model: query_results[col].model,
               id: res_obj[0],
               from: res_obj[1] };
    }

    // add first column
    for (var i=0; i<query_results[0].objects.length; i++) {
      entries.push([build_obj(0, query_results[0].objects[i])]);
    }

    // join rest of the columns
    for (var col=1; col<query_results.length; col++) {
      // console.log(query_results[col]);
      var new_entries = [];
      var column = query_results[col];
      var join_index = column.join_index;

      for (var i=0; i<entries.length; i++) {
        var row = entries[i];
        var objs = undefined;

        if (row[join_index] !== null) {
          var join_pk = row[join_index].id;
          objs = column.map[join_pk];
        }

        if (objs !== undefined) {
          for (var j=0; j<objs.length; j++) {
            var new_row = row;
            if (objs.length != 1) { new_row = row.slice(0); }
            if (objs[j][0] !== null) { new_row.push(build_obj(col, objs[j])); }
            else { new_row.push(null); }
            new_entries.push(new_row);
          }
        }
        else if (left_join_mode === true) {
          // The following will give you left join behavior in the display,
          // since it will create an empty row when it cannot extend a query.
          row.push(null);
          new_entries.push(row);
        }
      }
      entries = new_entries;
    }

    // create a dict of objects, add ptr to object from each cell in entries
    // table. this allows sharing of objects if there are duplicates in query
    // results.
    for (var i=0; i<entries.length; i++) {
      for (var j=0; j<entries[i].length; j++) {
        var entry = entries[i][j];
        if (entry !== null) {
          var obj_id = entry.model+'.'+entry.id;
          if (object_cache[obj_id] === undefined) {
            var id_str = ''+entry.id;
            object_cache[obj_id] = {id: {value: entry.id, display: id_str }};
          }
          entry['ptr'] = object_cache[obj_id];
        }
      }
    }

    models = [];
    // remeber each query's model
    for (var j=0; j<entries[0].length; j++) {
      var model_i = null;
      for (var i=0; i<entries.length; i++) {
        if (entries[i][j] !== null) { model_i = i; break; }
      }
      if (model_i === null) {
        alert('No model for a query. This is really bad!!!');
      }
      models.push({model: entries[model_i][j].model,
                   cols: 1,
                   attrs: [{name: 'id', visible: true}],
                   loaded: false});
    }
  }

  function _get_attr_value(value) {
    if (value && value.value !== undefined) {
      value = value.value;
      if (value && value.model && value.__str__ !== undefined) { return value.__str__; }
    }
    return value;
  }
    
  function _lc(s) { if (typeof s === 'string') { return s.toLowerCase(); } return s; }

  // add object data to cache
  function add_object_data(model, obj_data) {
    var id = obj_data.id;
    var obj_id = model+'.'+id;
    var ptr = object_cache[obj_id];
    if (ptr) {
      // it is possible we got data we didn't ask for, then ptr would be undefined
      ptr['__fetched__'] = obj_data;
      for (var a in obj_data) {
        // already has id field with link, don't overwrite that
        if (a === 'id') {
          var v = obj_data[a];
          var s = ''+v;
          if (obj_data['__url__']) { s = '<a href="'+obj_data['__url__']+'">'+v+'</a>'; }
          ptr[a] = {value: v, display: s};
        }
        else if (a !== '__url__') {
          // for each field, we have a value, and a display value that is shown
          // to the user.
          var v = obj_data[a];
          var s = v;
          if (v && v.model) {
            if ('__str__' in v) {
              s = v['__str__'];
              if (v.id) { s += ' ('+v.id+')'; }
            }
            if ('url' in v && v.url) { s = '<a href="'+v.url+'">'+s+'</a>'; }
          }
          ptr[a] = {value: v, display: s};
        }
      }
    }
  }

  // fetching objects from server or cache. calls callback with one arbitrary
  // object's data.
  function get_objects(model, ids, cb) {
    var cb_data = undefined;
    var unfetched = [];
    for (var i=0; i<ids.length; i++) {
      var id = ids[i];
      var obj_id = model+'.'+id;
      if (obj_id in object_cache && object_cache[obj_id]['__fetched__']) {
        cb_data = object_cache[obj_id]['__fetched__'];
      }
      else { unfetched.push(id); }
    }
    if (cb_data !== undefined && cb) { cb(cb_data); }

    if (unfetched.length > 0) {
      while (unfetched.length > 0) {
        var tofetch = unfetched.slice(0, GET_BATCH);
        var unfetched = unfetched.slice(GET_BATCH);
        outstanding_fetches += 1;
        get_objects_f(model, tofetch, function(results) {
          // console.log('parsing '+results.objects.length);
          outstanding_fetches -= 1;
          var fields = results.fields;
          for (var i=0; i<results.objects.length; i++) {
            var obj_data = {};
            // set URL
            obj_data['__url__'] = results.urls[i];
            // get object values
            var values = results.objects[i];
            for (var j=0; j<fields.length; j++) {
              obj_data[fields[j]] = values[j];
              if(Object.prototype.toString.call( values[j] ) === '[object Array]') {
                obj_data[fields[j]] = {
                  model: values[j][0],
                  id: values[j][1],
                  __str__: values[j][2],
                  url: values[j][3]
                }
              }
            }
            add_object_data(model, obj_data);
            if (cb_data === undefined && cb) {
              cb_data = obj_data;
              // console.log(obj_data);
              cb(obj_data);
            }
          }
        });
      }
    }
  }

  function csv() {
    if (tbl_rows.length == 0) { return ""; }
    var csv_rows = []

    var header = [];
    for (var i=0; i<tbl_attrs.length; i++) {
      var model;
      for (var j=0; j<tbl_rows.length; j++) {
        if (tbl_rows[j][i]) {
          model = tbl_rows[j][i].model;
          break;
        }
      }
      if (model !== undefined)
        header.push(model+'.'+tbl_attrs[i].name);
      else
        header.push(tbl_attrs[i].name);
    }
    csv_rows.push(header.join(','));

    for (var i=0; i<tbl_rows.length; i++) {
      var row = [];
      for (var j=0; j<tbl_rows[i].length; j++) {
        var entry = tbl_rows[i][j];
        if (entry) {
          var obj = entry.ptr;
          if (obj) {
            var v = obj[tbl_attrs[j].name];
            if (v && v.display !== undefined) { v = v.value; }
            if (v && v.__str__ !== undefined) { v = v.__str__; }
            if (v !== undefined && v !== null) { v = ''+v; }
            else { v = ''; }
            row.push(v);
          }
          else {
            if (tbl_attrs[j].name == 'id') { row.push(entry.id); }
            else { row.push(''); }
          }
        }
        else {
          row.push('');
        }
      }
      csv_rows.push(S(row).toCSV().s);
    }

    return csv_rows.join('\n');
  }

  function update_pourover(page_size) {
    var col_data = [];
    for (var i=0; i<tbl_rows.length; i++) {
      var d = {i: i, row: tbl_rows[i]};
      col_data.push(d);
    }
    pourover_collection = new PourOver.Collection(col_data);
    if (page_size === undefined) { page_size = DEFAULT_PAGE_SIZE; }
    tbl_view = new PourOver.View('default', pourover_collection, {page_size: page_size});
    tbl_controls = {};
    tbl_controls.left_join_mode = undefined;
    tbl_controls.sort_columns = [];
    tbl_controls.sort_dirs = [];
  }

  function next_page() { tbl_view.page(1); }
  function prev_page() { tbl_view.page(-1); }

  function clear_sort() {
    pourover_collection.sorts = {};
    tbl_controls.sort_columns = [];
    tbl_controls.sort_dirs = [];
  }

  function sort(column_index) {
    function _sorter_name() {
      var n = [];
      for (var i=0; i<tbl_controls.sort_columns.length; i++) {
        var col = tbl_controls.sort_columns[i];
        var rev = tbl_controls.sort_dirs[i];
        n.push(col);
        n.push(rev);
      }
      return n.join(',');
    }

    function _make_sorter_class() {
      var cmp_by_col = function(col, attr, reverse, a, b) {
        if (a.row[col].ptr[attr] === undefined) { return 1; }
        if (b.row[col].ptr[attr] === undefined) { return -1; }
        var v_a = a.row[col].ptr[attr];
        var v_b = b.row[col].ptr[attr];
        v_a = _get_attr_value(v_a);
        v_b = _get_attr_value(v_b);
        if (reverse) {
          var tmp = v_a;
          v_a = v_b;
          v_b = tmp;
        }
        if (v_a === undefined || v_a === null) { return 1; }
        if (v_b === undefined || v_b === null) { return -1; }
        if (v_a > v_b) { return -1; }
        else if (v_a < v_b) { return 1; }
        else { return 0; }
      }

      var ColSorter = PourOver.Sort.extend({
        fn: function(a, b) {
          for (var i=0; i<tbl_controls.sort_columns.length; i++) {
            var col = tbl_controls.sort_columns[i];
            var rev = tbl_controls.sort_dirs[i];
            var attr = tbl_attrs[col].name;
            var r = cmp_by_col(col, attr, rev, a, b);
            if (r != 0) { return r; }
          }
          return 0;
        }
      });
      return ColSorter;
    }

    // can only sort if we have all the data
    if (partial_fetch !== undefined || outstanding_fetches > 0) { return; }

    var i = tbl_controls.sort_columns.indexOf(column_index);
    if (i >= 0) {
      // switch direction
      if (tbl_controls.sort_dirs[i] === true) { tbl_controls.sort_dirs[i] = false; }
      else { tbl_controls.sort_dirs[i] = true; }
    }
    else {
      tbl_controls.sort_columns.push(column_index);
      tbl_controls.sort_dirs.push(true);
    }

    // create new sorter
    var sorter_name = _sorter_name();
    var Sorter = _make_sorter_class();
    var sorters = [new Sorter(sorter_name)]
    pourover_collection.addSorts(sorters);
    tbl_view.setSort(sorter_name);
  }

  function make_filter(column_index) {
    // can only filter if we have all the data
    if (partial_fetch !== undefined || outstanding_fetches > 0) { return; }

    var attr = tbl_attrs[column_index].name;

    var colFilter = PourOver.Filter.extend({
      cacheResults: function(items){
        var possibilities = this.possibilities;
        _(items).each(function(i){
          var value = i.row[column_index].ptr[attr];
          value = _get_attr_value(value)
          if (value === undefined || value === null) { value = ''; }
          else { value = _lc(value); }
          _(possibilities).each(function(p){
            if (_lc(p.value) === value) {
              p.matching_cids = PourOver.insert_sorted(p.matching_cids,i.cid)
            }
          })
        });
      },
      addCacheResults: function(new_items){ this.cacheResults.call(this, new_items); },
      getFn: function(query){
        var query_lc = _lc(query);
        var matching_possibility = _(this.possibilities).find(function(p){
              var value_lc = _lc(p.value);
              return value_lc === query_lc;
            });
        return this.makeQueryMatchSet(matching_possibility.matching_cids, query)
      }
    });

    var _mk_filter = function(name, values, attr){
      var values = _(values).map(function(i){ return {value:i} }),
          opts = {associated_attrs: [attr], attr: attr},
          filter = new colFilter(name, values, opts);
      return filter;
    }

    var possibilities = [];
    for (var i=0; i<tbl_rows.length; i++) {
      var v = tbl_rows[i][column_index].ptr[attr];
      v = _get_attr_value(v);
      if (v === undefined || v === null) { v = ''; }
      if (possibilities.indexOf(v) < 0) { possibilities.push(v); }
    }

    var column_filter = _mk_filter("col_"+column_index+"_filter", possibilities, attr);
    pourover_collection.addFilters([column_filter])

    if (tbl_controls.filters === undefined) { tbl_controls.filters = {}; }
    tbl_controls.filters[column_index] = possibilities;
    // console.log('adding filter '+column_filter.name);
    // console.log(possibilities);
  }

  function filter(column_index, value) {
    var filter_name = 'col_'+column_index+'_filter';
    var filter = pourover_collection.filters[filter_name];
    if (value !== undefined) {
      filter.query(value);
      pourover_collection.get(filter.current_query.cids);
      if (tbl_controls.filtered === undefined) { tbl_controls.filtered = {}; }
      tbl_controls.filtered[column_index] = value;
    }
    else {
      filter.clearQuery();
      pourover_collection.get(filter.current_query.cids);
      if (tbl_controls.filtered === undefined) { tbl_controls.filtered = {}; }
      tbl_controls.filtered[column_index] = undefined;
    }
    tbl_controls.aggregates = {}
  }

  function aggregate(column_index) {
    var attr = tbl_attrs[column_index].name;
    var objs = pourover_collection.get(tbl_view.match_set.cids);
    var counts = {};
    for (var i=0; i<objs.length; i++) {
      var v = objs[i].row[column_index].ptr[attr];
      v = _get_attr_value(v);
      v = _lc(v);
      if (v === undefined || v === null) { v = ''; }
      if (counts[v] === undefined) { counts[v] = 0; }
      counts[v] += 1;
    }
    if (tbl_controls.aggregates === undefined) { tbl_controls.aggregates = {}; }
    tbl_controls.aggregates[column_index] = counts;
  }

  function update_csv() {
    if (tbl_csv) { tbl_csv = csv(); }
  }

  // update table data structure after receiving new attrs for unfetched
  // objects in the table.
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

    update_pourover(); // use PourOver for paging
    update_csv(); // update CSV if user had requested it
    update_controller(); // update controller that our table has expanded
  }

  function update_controller() {
    // tell angular to re-render
    set_table_cb({
      queries: models,
      left_join_mode: left_join_mode,
      attrs: tbl_attrs,
      length: tbl_rows.length,
      view: tbl_view,
      controls: tbl_controls,
      csv: tbl_csv,
      // actions
      toggleQuery: toggle,
      showCSV: show_csv,
      nextPage: next_page,
      prevPage: prev_page,
      sort: sort,
      clearSort: clear_sort,
      makeFilter: make_filter,
      filter: filter,
      aggregate: aggregate,
      partial_fetch: partial_fetch,
      fetchAll: fetch_all,
      createTable: create_table
    });
  }

  // after fetching the first object from a query's results, update the query
  // model attributes list.
  function update_model_attrs(query_idx, object) {
    if (models[query_idx].attrs.length == 1) {
      var old_attr = models[query_idx].attrs[0];
      var attrs = [];
      for (var a in object) { if (a !== 'id' && a !== '__url__') { attrs.push({name: a, visible: true}); } }
      attrs.sort(function(a, b) {
        if (a.name < b.name) { return -1; }
        else if (a.name > b.name) { return 1; }
        return 0;
      });
      attrs.unshift(old_attr);
      models[query_idx].attrs = attrs;
      models[query_idx].cols = attrs.length;

      update_table();
    }
  }

  function fetch_all() {
    partial_fetch = undefined;
    update_controller();

    for (var i=0; i<models.length; i++) {
      if (models[i].attrs.length > 1) { show_object_attrs(i); }
    }
  }

  // show attributes for a query's objects
  function show_object_attrs(query_idx) {
    if (models[query_idx].loaded == true) {
      // already loaded, mark attrs as visible
      for (var i=0; i<models[query_idx].attrs.length; i++) {
        models[query_idx].attrs[i].visible = true;
      }
      models[query_idx].cols = models[query_idx].attrs.length;
      return;
    }

    // fetch objects from server
    var ids = [];
    var nfetch = entries.length;
    if (partial_fetch !== undefined) { nfetch = partial_fetch; }
    if (nfetch > entries.length) { nfetch = entries.length; }
    for (var i=0; i<nfetch; i++) {
      var entry = entries[i][query_idx];
      if (entry !== null) { ids.push(entry.ptr.id.value); }
      // console.log('will fetch '+entry.ptr.id.value);
    }
    get_objects(models[query_idx].model, ids, function(data) {
      update_model_attrs(query_idx, data);
      if (partial_fetch === undefined) { models[query_idx].loaded = true; }
    }, function() {
      // console.log('all fetch completed');
    });
  }

  // hide attributes for a query's objects
  function hide_object_attrs(query_idx) {
    // mark attrs as invisible, leaving only the 'id' attr
    for (var i=0; i<models[query_idx].attrs.length; i++) {
      if (models[query_idx].attrs[i].name !== 'id') {
        models[query_idx].attrs[i].visible = false;
      }
    }
    models[query_idx].cols = 1;
  }

  function toggle(query_idx) {
    if (models[query_idx].cols == 1) { show_object_attrs(query_idx); }
    else { hide_object_attrs(query_idx); }
  }

  function show_csv() {
    tbl_csv = csv();
    update_controller();
  }

  function create_table(lj) {
    process_results(lj);
    update_table(); // initialize table
    if (entries.length > PARTIAL_FETCH) { partial_fetch = GET_BATCH; }
    else { partial_fetch = undefined; }

    // by default, fetch objects from last query
    if (entries.length > 0 && entries[0].length > 0) {
      show_object_attrs(entries[0].length-1);
    }
  }

  create_table(false);
}
