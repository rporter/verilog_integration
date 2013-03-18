$report = function(){
};

(function($report) {

  $report.levels = {
    INT_DEBUG   : 0,
    DEBUG       : 1,
    INFORMATION : 2,
    NOTE        : 3,
    SUCCESS     : 4,
    WARNING     : 5,
    ERROR       : 6,
    INTERNAL    : 7,
    FATAL       : 8
  };

  $report.report = function(){
    var report;
    return function(){
      return report || (report = $('#report'));
    };
  }();
  $report.tabs = function(){
    var tabs;
    return function(){
	return (tabs || (tabs = $report.report().tabs)).apply($report.report(), arguments);
    };
  }();
  $report.tab_id = function() {
    var id;
    return function() {
      id = (id===undefined)?0:id+1;
      return 'log-'+id;
    }
  }();

  $report.hijax = function(panel){ 
    $('a', panel).click(function() { 
      if (this.href == '') return true;
       /**makes children 'a' on panel load via ajax, hence hijax*/ 
       $(panel).load(this.href, null, function(){ 
         /**recursively apply the hijax to newly loaded panels*/ 
         hijax(panel);                   
       }); 
       /**prevents propagation of click to document*/ 
       return false; 
    });     
  };

  function testJSON(data) {
      var get = function(severity, attr) {
        var result = this.msgs.filter(function(a){return a.severity === severity})[0];
        if (attr === undefined) return result;
	if (result === undefined) return '';
        if (attr instanceof Function) {
          return attr(result);
	} else if (result.hasOwnProperty(attr)) {
          return result[attr];
        }
        return '';
      }
      var status = function() {
          var sorted = this.msgs.sort(function(a,b){return a.level<b.level});
          if (sorted[0].level>=$report.levels.ERROR) {
              return {status: 'FAIL', reason : '('+sorted[0].severity+') '+sorted[0].msg};
          }
          var success = this.get('SUCCESS');
          if (success === undefined) {
              return {status: 'FAIL', reason : 'No SUCCESS'};
	  }
          if (success.count > 1) {
              return {status: 'FAIL', reason : 'Too many SUCCESSes'};
	  }
	  return {status : 'PASS', reason : success.msg};
      };

    this.cols = function() {
      return [
	{ "sTitle": "log id" },
	{ "sTitle": "user" },
	{ "sTitle": "description" },
	{ "sTitle": "fatals" },
	{ "sTitle": "internals" },
	{ "sTitle": "errors" },
	{ "sTitle": "warnings" },
	{ "sTitle": "message" },
	{ "sTitle": "status" }
      ];
    };

    this.rows = function() {
        function popup(attr) {
            return '<abbr title="'+attr.msg.replace('"', '&quot;')+'">'+attr.count+'</abbr>';
	}
	return data.map(function(log){
            var status = log.status();
            return [log.log.log_id, log.log.user, log.log.description, log.get('FATAL', popup), log.get('INTERNAL', popup), log.get('ERROR', popup), log.get('WARNING', popup), status.reason, status.status];
	});
    };
		       
      for (log in data) {
          data[log].get    = get;
          data[log].status = status;
     }
  };

  $report.renderTestJSON = function(data, type) {
    data = new testJSON($.parseJSON(data));
    var container = $('<div><table class="display"></table></div>');
    $('table', container).dataTable({
      "bJQueryUI": true,
      "bPaginate": false,
      "bFilter": false,
      "aaData" : data.rows(),
      "aoColumns": data.cols(),
      "aaSorting": [[0, "desc"]],
      "fnRowCallback": function(nRow, aData, iDisplayIndex) {
	  $(nRow).bind('click.example', {log_id : aData[0]}, $report.openLogTab)
      }
    });
    return container;
  };

   $report.openLogTab = function(event) {
    var id  = $report.tab_id();
    var div = $('<div/>', {class: "tab", id:id});
    div.appendTo($report.report());
    $.ajax({
      url : 'msgs/'+event.data.log_id,
      dataType : 'json',
      success : function (json) {
	json.forEach(function(msg) {
            $('<code/>', {text:msg.msg}).appendTo(div);
	});
      },
      error : function(xhr, status, index, anchor) {
        console.log(xhr, status, index);
      }
    });
    $report.tabs('add', '#'+id, event.data.log_id+' log');
  };

})($report);

