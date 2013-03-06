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
	if (result !== undefined && result.hasOwnProperty(attr)) return result[attr];
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
	return data.map(function(log){
            var status = log.status();
            return [log.log.log_id, log.log.description, log.get('FATAL', 'count'), log.get('INTERNAL', 'count'), log.get('ERROR', 'count'), log.get('WARNING', 'count'), status.reason, status.status];
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
      "sPaginationType": "full_numbers",
      "aaData" : data.rows(),
      "aoColumns": data.cols()
    });
    return container;
  };

})($report);

