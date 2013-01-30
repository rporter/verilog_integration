$report = function(){
};

(function($report) {
  $report.report = function(){
    var report;
    return function(){
      return report || (report = $('#report'));
    };
  }();
  $report.tabs = function(){
    var tabs;
    return function(){
	return tabs || (tabs = $report.report().tabs.apply($report.report(), arguments));
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
})($report);

