window.JST = window.JST || {};
var template = function(str){var fn = new Function('obj', 'var __p=[],print=function(){__p.push.apply(__p,arguments);};with(obj||{}){__p.push(\''+str.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/<%=([\s\S]+?)%>/g,function(match,code){return "',"+code.replace(/\\'/g, "'")+",'";}).replace(/<%([\s\S]+?)%>/g,function(match,code){return "');"+code.replace(/\\'/g, "'").replace(/[\r\n\t]/g,' ')+"__p.push('";}).replace(/\r/g,'\\r').replace(/\n/g,'\\n').replace(/\t/g,'\\t')+"');}return __p.join('');");return fn;};
window.JST['query'] = template('<!-- join queries -->\n<div class="well">\n  <div class="input-group" ng-repeat="join_query in query.form.prev_joins track by $index">\n    <span class="input-group-addon">Joined</span>\n    <input class="form-control" ng-model="join_query" disabled />\n  </div>\n  <div ng-if="query.form.last_join">\n    <form ng-submit="query.extendJoin()">\n      <div class="input-group">\n        <span class="input-group-addon">Join</span>\n        <input class="form-control" ng-model="query.form.last_join" />\n      </div>\n    </form>\n  </div>\n  <form ng-submit="query.newJoin()">\n    <div class="input-group">\n      <span class="input-group-addon">New Join</span>\n      <input class="form-control" ng-model="query.form.new_join" />\n    </div>\n  </form>\n</div>\n\n<p ng-if="query.query_error">\n  <span class="label label-danger">Query Syntax Error</span>\n  <code>{{ query.query_error }}</code>\n</p>\n\n<p ng-if="search_error">\n  <span class="label label-danger">Search Error</span>\n  {{ search_error }}\n</p>\n\n<p ng-if="completed && success && !last_model">\n  <em>No matching data</em>\n</p>\n\n<div ng-if="completed && success && last_model">\n\n<div id="results-header">\n  <span>{{ table.rows.length }} row(s) of <b>{{ last_model }}</b></span>\n  <div id="recommended_rels" class="dropdown navbar-right">\n    <a data-toggle="dropdown" href="javascript:void(0);">Relations from {{ last_model }}</a>\n    <ul class="rel-list dropdown-menu" role="menu">\n      <li ng-repeat="rel in last_model_rels">\n        <span class="rel-actions">\n          <span ng-if="!query.form.last_join && query.form.prev_joins.length == 0">\n            <a class="btn btn-xs btn-info" href=\'javascript:void(0);\' title="Extend main query"\n               ng-click="newMainQuery(query.form.main_query, last_model, rel)">Q</a>\n          </span>\n          <span ng-if="query.form.last_join">\n            <a class="btn btn-xs btn-info" href=\'javascript:void(0);\' title="Extend last join"\n               ng-click="query.addRelToJoin(last_model, rel)">E</a>\n          </span>\n          <a class="btn btn-xs btn-info" href=\'javascript:void(0);\' title="New join"\n             ng-click="query.addJoinToQuery(last_model, rel)">J</a>\n        </span>\n        <span class="rel-name">{{ rel }}</span>\n      </li>\n    </ul>\n  </div> <!-- recommended_rels -->\n</div>\n\n<table class="table table-condensed table-striped table-bordered table-fixed" ng-if="table.attrs">\n  <tr class="success">\n    <td class="wrap" ng-repeat="q in table.queries track by $index" colspan="{{ q.cols }}">\n      <a href="javascript:void(0)" ng-click="table.toggle($index)" title="Click to show/hide attrs"\n       >{{ q.query }}</a>\n    </td>\n  </tr>\n\n  <tr class="success">\n    <th class="wrap" ng-repeat="attr in table.attrs track by $index">{{ attr }}</th>\n  </tr>\n\n  <tr ng-repeat="row in table.rows track by $index">\n    <td class="wrap" ng-repeat="object in row track by $index">\n      {{ object.ptr[table.attrs[$index]]|showAttr }}\n    </td>\n  </tr>\n</table>\n\n<p>\n<a href="data:attachment/csv,{{ table.csv }}" target="_blank" download="data.csv">Click to download</a>\n</p>\n\n</div> <!-- if for results table -->\n');
window.JST['search'] = template('<div class="container-fluid">\n\n<p>\n  <a href="#/" class="lead">Curious</a>\n</p>\n\n<div class="well">\n  <form ng-submit="submitQuery()">\n    <div class="input-group">\n      <span class="input-group-addon">Query</span>\n      <input class="form-control" ng-model="query" ng-change="delayCheckQuery()" />\n    </div>\n  </form>\n</div>\n\n<p ng-if="query_error">\n  <span class="label label-danger">Query Syntax Error</span>\n  <code>{{ query_error }}</code\n</p>\n\n<p ng-if="query_accepted">\n  <span class="label label-info">Valid Query</span>\n  <code>{{ query_accepted }}</code>\n</p>\n\n<div id="results">\n  <div ng-repeat="query in query_submitted">\n    <partial template="query" ng-controller="QueryController"></partial>\n  </div>\n</div>\n\n<div id="queries">\n  <p><h4>Recent Queries</h4></p>\n  <div ng-repeat="query in recent_queries">\n    <a href="#/q/{{ query|encodeURI }}">{{ query }}</a>\n  </div>\n</div>\n\n</div> <!-- container-fluid -->\n');
