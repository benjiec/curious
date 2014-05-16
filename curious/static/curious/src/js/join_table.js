// A JoinTable manages objects returned by a query. JoinTable exposes a data
// structure that angular template can easily use to display the objects and
// their attributes.

function curiousJoinTable(results, set_table_cb, object_cache_f, get_objects_f) {
  // Constructor:
  //   results        - array of search results, each result has a model and a
  //                    list of object output input tuples
  //   set_table_cb   - callback to set table data structure, should take a hash
  //   object_cache_f - function to call to get object cache
  //   get_objects_f  - function to fetch objects in batch, should take a model
  //                    and an ids list

  var GET_BATCH = 500;  // how many objects to fetch from server at a time
  var DEFAULT_PAGE_SIZE = 100;
  var PARTIAL_FETCH = 3000; // auto fetch all when total is below this threshold

  var entries = [];
  var models = [];

  // public variables sent to set_table_cb
  var tbl_queries = [];
  var tbl_attrs = [];
  var tbl_rows = [];
  var tbl_view = undefined;
  var tbl_csv = undefined;
  var tbl_controls = {};
  var partial_fetch = undefined;
  var pourover_collection = undefined;
  var pourover_sorters = undefined;
  var outstanding_fetches = 0;

  // get reference to object cache once
  var object_cache = object_cache_f();

  // from results, construct entries table - joining results together

  // for each result, build dict indexed by object id
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

  // create a dict of objects, add ptr to object from each cell in entries
  // table. this allows sharing of objects if there are duplicates in query
  // results.
  for (var i=0; i<entries.length; i++) {
    for (var j=0; j<entries[i].length; j++) {
      var entry = entries[i][j];
      var obj_id = entry.model+'.'+entry.id;
      if (object_cache[obj_id] === undefined) {
        var id_str = ''+entry.id;
        if (entry.url) { id_str = '<a href="'+entry.url+'">'+entry.id+'</a>'; }
        object_cache[obj_id] = {id: {value: entry.id, display: id_str }};
      }
      entry['ptr'] = object_cache[obj_id];
    }
  }

  // remeber each query's model
  for (var j=0; j<entries[0].length; j++) {
    tbl_queries.push({model: entries[0][j].model, cols: 1});
    models.push({model: entries[0][j].model,
                 attrs: [{name: 'id', visible: true}],
                 loaded: false});
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
          if ('url' in v && v.url) { s = '<a href="'+v.url+'">'+s+'</a>'; }
        }
        ptr[a] = {value: v, display: s};
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

    var row0 = tbl_rows[0];
    var header = [];
    for (var i=0; i<tbl_attrs.length; i++) {
      var model = row0[i].model;
      header.push(model+'.'+tbl_attrs[i].name);
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
            if (v.display) { v = v.value; }
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
            if (tbl_attrs[j].name == 'id') { row.push(entry.id); }
            else { row.push(''); }
          }
        }
        else {
          if (tbl_attrs[j].name == 'id') { row.push(entry.id); }
          else { row.push(''); }
        }
      }
      csv_rows.push(row.join(','));
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
    pourover_sorters = {};
    if (page_size === undefined) { page_size = DEFAULT_PAGE_SIZE; }
    tbl_view = new PourOver.View('default', pourover_collection, {page_size: page_size});
    tbl_controls = {};
  }

  function next_page() { tbl_view.page(1); }
  function prev_page() { tbl_view.page(-1); }

  function sort(column_index) {
    function _sorter_name(col, reverse) {
      if (reverse) { return '_dsc_col_'+col; }
      else { return '_asc_col_'+col; }
    }

    function _make_sorter_class(col, attr, reverse) {
      var ColSorter = PourOver.Sort.extend({
        fn: function(a, b) {
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
      });
      return ColSorter;
    }

    function _create_sorter(col) {
      var asc_sorter_name = _sorter_name(col, false);
      var dsc_sorter_name = _sorter_name(col, true);

      if (pourover_sorters[asc_sorter_name] === undefined) {
        var ColSorterAsc = _make_sorter_class(col, tbl_attrs[col].name, true);
        var ColSorterDsc = _make_sorter_class(col, tbl_attrs[col].name, false);
        var sorters = [new ColSorterAsc(asc_sorter_name), new ColSorterDsc(dsc_sorter_name)];
        pourover_sorters[asc_sorter_name] = sorters;
        pourover_collection.addSorts(sorters);
      }

      return [asc_sorter_name, dsc_sorter_name];
    }

    // can only sort if we have all the data
    if (partial_fetch !== undefined || outstanding_fetches > 0) { return; }

    // dynamically create a sorter if none exists for that column
    var sorters = _create_sorter(column_index);
    var sorter;

    if (tbl_controls.sort_column !== undefined && tbl_controls.sort_column === column_index) {
      if (tbl_controls.sort_asc === false) {
        tbl_controls.sort_asc = true;
        sorter = sorters[0];
      }
      else {
        tbl_controls.sort_asc = false;
        sorter = sorters[1];
      }
    }
    else {
      tbl_controls.sort_column = column_index;
      tbl_controls.sort_asc = true;
      sorter = sorters[0];
    }

    tbl_view.setSort(sorter);
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
      queries: tbl_queries,
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
      make_filter: make_filter,
      filter: filter,
      aggregate: aggregate,
      partial_fetch: partial_fetch,
      fetchAll: fetch_all
    });
  }

  // after fetching the first object from a query's results, update the query
  // model attributes list.
  function update_model_attrs(query_idx, object) {
    if (models[query_idx].attrs.length == 1) {
      var old_attr = models[query_idx].attrs[0];
      var attrs = [];
      for (var a in object) { if (a !== 'id') { attrs.push({name: a, visible: true}); } }
      attrs.sort(function(a, b) { return a.name-b.name; });
      attrs.unshift(old_attr);
      models[query_idx].attrs = attrs;
      tbl_queries[query_idx].cols = attrs.length;

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
      tbl_queries[query_idx].cols = models[query_idx].attrs.length;
      return;
    }

    // fetch objects from server
    var ids = [];
    var nfetch = entries.length;
    if (partial_fetch !== undefined) { nfetch = partial_fetch; }
    if (nfetch > entries.length) { nfetch = entries.length; }
    for (var i=0; i<nfetch; i++) {
      var entry = entries[i][query_idx];
      ids.push(entry.ptr.id.value);
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
    tbl_queries[query_idx].cols = 1;
  }

  function toggle(query_idx) {
    if (tbl_queries[query_idx].cols == 1) { show_object_attrs(query_idx); }
    else { hide_object_attrs(query_idx); }
  }

  function show_csv() {
    tbl_csv = csv();
    update_controller();
  }

  update_table(); // initialize table
  if (entries.length > PARTIAL_FETCH) { partial_fetch = GET_BATCH; }

  // by default, fetch objects from last query
  if (entries.length > 0 && entries[0].length > 0) {
    show_object_attrs(entries[0].length-1);
  }
}
