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

  function csv_string() {
    var A = [['n','sqrt(n)']];
    for(var j=1; j<10; ++j){ 
      A.push([j, Math.sqrt(j)]);
    }
    var csvRows = [];
    for(var i=0, l=A.length; i<l; ++i){
      csvRows.push(A[i].join(','));
    }
    var csvString = csvRows.join("%0A");
    return csvString;
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

    // tell angular to re-render
    set_table_cb({
      toggle: toggle,
      csv: csv_string,
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

  update_table(); // initialize table
  // by default, fetch objects from last query
  show_object_attrs(entries[0].length-1);
}
