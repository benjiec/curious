// A JoinTable manages objects returned by a set of join queries. JoinTable
// exposes a data structure that angular template can easily use to display the
// objects and their attributes.

function curiousJoinTable(results, set_table_cb, get_objects_f) {
  // Constructor:
  //   results       - array of search results, each result has a model and a
  //                  list of object output input tuples
  //   set_table_cb  - callback to set table data structure, should take a hash
  //   get_objects_f - function to fetch objects in batch, should take a model and an ids list

  var GET_BATCH = 500;  // how many objects to fetch from server at a time

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

  // add object data to cache
  function add_object_data(model, obj_data) {
    var id = obj_data.id;
    var obj_id = model+'.'+id;
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
  }

  // fetching objects from server or cache. calls callback with one arbitrary
  // object's data.
  function get_objects(model, ids, cb) {
    var cb_data = undefined;
    var unfetched = [];
    for (var i=0; i<ids.length; i++) {
      var id = ids[i];
      var obj_id = model+'.'+id;
      if (obj_id in objects && objects[obj_id]['__fetched__']) {
        cb_data = objects[obj_id]['__fetched__'];
      }
      else { unfetched.push(id); }
    }
    if (cb_data !== undefined && cb) { cb(cb_data); }

    if (unfetched.length > 0) {
      while (unfetched.length > 0) {
        var tofetch = unfetched.slice(0, GET_BATCH);
        var unfetched = unfetched.slice(GET_BATCH);
        get_objects_f(model, tofetch, function(results) {
          for (var i=0; i<results.length; i++) {
            var obj_data = results[i];
            add_object_data(model, obj_data);
            if (cb_data === undefined && cb) {
              cb_data = obj_data;
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
      get_objects(obj.model, [obj.id], function(data) {
        update_model_attrs(query_idx, data);
      });
      return;
    }

    // fetch every object from server
    var ids = [];
    for (var i=0; i<entries.length; i++) {
      var entry = entries[i][query_idx];
      ids.push(entry.ptr.id.value);
      // console.log('will fetch '+entry.ptr.id.value);
    }

    get_objects(models[query_idx].model, ids, function(data) {
      update_model_attrs(query_idx, data);
    });
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
