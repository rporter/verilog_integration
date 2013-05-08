// Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

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
    FATAL       : 8,
    _SIZE       : 9,
    severity    : function (level) {
      for (var l in this) {
        if (this[l] === level) {
          return l;
	}
      }
    }
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

  $report.testJSON = function(data){

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

    this.render = function() {
      var container = $('<div><table class="display"></table></div>');
      $('table', container).dataTable({
        "bJQueryUI": true,
        "bPaginate": false,
        "bFilter": false,
        "aaData" : this.rows(),
        "aoColumns": this.cols(),
        "aoColumnDefs": [
                {
                    "aTargets":[this.cols().length-1], // last col
                    "fnCreatedCell": function(nTd, sData, oData, iRow, iCol) {
                        $(nTd).addClass(sData);
                    },                   
                }
        ],
        "aaSorting": [[0, "desc"]],
        "fnRowCallback": function(nRow, aData, iDisplayIndex) {
            $(nRow).bind('click.example', {log_id : aData[0], children : aData[8], anchor : $report.report()},
              function(event) {
                var log;
                if (event.data.children) {
                  // this will be a tab-within-tab
                  log = new $report.openRegr(event.data);
                } else {
                  // place report log in new tab
                  log = new $report.openLog(event.data);
                }
                log.add($report.tabs());
              }
            );
        }
      });
      return container;
    }

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
	{ "sTitle": "children" },
	{ "sTitle": "status" },
      ];
    };

    this.rows = function() {
        function popup(attr) {
            return '<abbr title="'+attr.msg.replace('"', '&quot;')+'">'+attr.count+'</abbr>';
	}
	return data.map(function(log){
            return [log.log.log_id, log.log.user, log.log.description, log.get('FATAL', popup), log.get('INTERNAL', popup), log.get('ERROR', popup), log.get('WARNING', popup), log.status.reason, log.log.children, log.status.status];
	});
    };

    // attach methods to individual data		       
    for (log in data) {
      data[log].get = get;
    }
    
  };

  $report.openLog = function(data, anchor) {
    var self = this;
    this.id  = $report.tab_id();
    this.div = $('<div/>', {class: "tab", id:self.id});
    anchor = anchor || data.anchor;

    this.widget = function() {
      function has_ident(json) {
        return json[0].ident !== null || (json.length > 1 && has_ident(json.splice(1)));
      }
      var nodes  = $('code', self.div);
      var widget = $('<div class="widget"/>').appendTo(self.div);
      var align  = function() {
        widget.animate({top:$(self.div).scrollTop()},{duration:100,queue:false});
      };
      $(this.div).scroll(align);
      // show/hide timestamp
      $('<input type="checkbox">').appendTo(widget).bind('change.time', function(event){$('time', self.div).toggle()}).wrap('<p>Show time</p>');
      var ident =  $('<input type="checkbox">').appendTo(widget).bind('change.tag', function(event){$('ident', self.div).toggle()}).wrap('<p>Show ident</p>');
      if (has_ident(self.json)) {
        ident.trigger('click');
      } else {
        ident.prop('title', 'there are no given idents');
      }
      // filter by severity
      var slider = $('<div class="slider"/>').appendTo(widget);
      var lower  = $("<div/>").css({ position : 'absolute' , top : 10, left : 0 }).text($report.levels.severity(0)).hide();
      var upper  = $("<div/>").css({ position : 'absolute' , top : 10, left : 0 }).text($report.levels.severity($report.levels._SIZE-1)).hide();
      slider.slider({
        range: true,
        min: 0,
        max: $report.levels._SIZE-1,
        values: [ 0, $report.levels._SIZE-1 ]
      }).bind('slide.example', function(event, ui) {
        self.div.hide();
        lower.text($report.levels.severity(ui.values[0]));
        upper.text($report.levels.severity(ui.values[1]));
        nodes.each(function(index){if(($(this).attr('level') >= ui.values[0]) && ($(this).attr('level') <= ui.values[1])){$(this).show()}else{$(this).hide()}})
        self.div.show();
      });
      slider.find(".ui-slider-handle:first")
        .append(lower)
        .bind('mouseenter.example', function(event){lower.show()})
        .bind('mouseleave.example', function(event){lower.hide()});
      slider.find(".ui-slider-handle:last")
        .append(upper)
        .bind('mouseenter.example', function(event){upper.show()})
        .bind('mouseleave.example', function(event){upper.hide()});
      // message indexed by severity
      function getBySeverity() {
        function sorted(nodes) {
          function children(nodes) {
            return nodes.slice(0,11).map(
              function(it, idx){
                return {
                  "title"    : (idx>9)?'...':$report.levels.severity(parseInt($(it).attr('level'))),
                  "key"      : it.idx
                };
            });
          };
          return Object.keys(nodes).sort().map(
            function(it) {
              return {
        	      "title"    : '(' + it.slice(1) + ') ' + $report.levels.severity(parseInt(it.slice(1))) + ' <s' + parseInt(it.slice(1))/10 + '><i>' + nodes[it].length + '</i></s>',
                "key"      : nodes[it][0].idx,
                "children" : children(nodes[it])
             }}
          );
        };
  	return sorted(nodes.toArray().reduce(function(levels, node, idx) {
          var level = 's'+$(node).attr('level');
          node.idx = idx;
          if (!levels.hasOwnProperty(level)) levels[level]=[];
          levels[level].push(node);
          return levels;
        }, {}));
      }
  
      var msgIndex = $('<div/>').appendTo(widget);
      msgIndex.dynatree({
        children : [
            {title : "Messages", isFolder : true, children : getBySeverity(nodes)},
        ],
        onActivate: function(node) {
            self.div.animate({scrollTop : $(nodes[node.data.key]).offset().top - self.div.offset().top + self.div.scrollTop() - self.div.height()/2});
        },
        onRender : function(dtnode, nodeSpan) {
          $('a', dtnode.li).hover(
            function(){$(nodes[$.ui.dynatree.getNode(this).data.key]).addClass(   'example-highlight')},
            function(){$(nodes[$.ui.dynatree.getNode(this).data.key]).removeClass('example-highlight')}
          );
          align();
        }
      });
    }

    this.add = function(tabs) {
      tabs.tabs('add', '#'+self.id, data.log_id+' log');
    }

    this.div.appendTo(anchor);
    $.ajax({
      url : 'msgs/'+data.log_id,
      dataType : 'json',
      success : function(data) {
        self.json = data;
        self.div.jqoteapp('#template', self.json);
        self.widget();
      },
      error : function(xhr, status, index) {
        console.log(xhr, status, index);
      }
    });

  };

  $report.openLog.justify = function (c, l) {
    l = l || 12;
    return Array(l).join(' ').substr(c.length) + c;
  }
  $report.openLog.msg = function (m) {
    return m.replace(/>/g, '&gt;').replace(/</g, '&lt;');
  }

  $report.openHier = function(data, anchor){
    var self = this;
    this.id  = $report.tab_id();
    this.div = $('<div>', {id : this.id});

    // find all logs with given parent id and return with children
    // in extreme cases it will be more expedient to do this on the server
    // as output is grouped by parent
    this.build = function build(parent) {
      return self.json.filter(
        function(it){
          if (it.log.parent === parent) {
            it.children = build(it.log.log_id);
            return true;
          }
          return false;
        });
    };

    this.add = function(tabs) {
      tabs.tabs('add', '#'+self.id, data.log_id+' hier');
    };

    this.table = function(log_id, anchor) {
      anchor.html((new $report.testJSON(self.json)).render());
    };

    this.pane = function() {
      function hier(json) {
        return json.map(function(it){return {title : it.log.description + '(' + it.log.log_id + ')', isFolder : it.children.length, key : it.log.log_id, children : hier(it.children || [])}});
      }
      var explorer = $('<div class="explorer">');
      var children = $('<div class="children">');
      var tree = $('<div>').dynatree({
        children : [
            {title : "ALL", isFolder : true, key : null, children : hier(self.json)},
            hier(self.tree)[0]
        ],
        onActivate: function(node) {
          self.table(node.data.key, children);
        },
      });
      explorer.append(tree);
      this.div.append(explorer, children);
    }

    this.div.appendTo(anchor);
    $.ajax({
      url : 'rgr/'+data.log_id,
      dataType : 'json',
      success : function(data) {
        self.json = data;
        self.tree = self.build(null);
        self.pane();
      },
      error : function(xhr, status, index) {
        console.log(xhr, status, index);
      }
    });
  }


  $report.openRegr = function(data){
    var self = this;
    this.id  = $report.tab_id();
    this.div = $('<div>', {id : this.id}).append('<ul>');
    this.add = function(tabs) {
      tabs.tabs('add', '#'+self.id, data.log_id+' regr');
    };

    this.div.appendTo(data.anchor);
    this.tabs = this.div.tabs();

    this.hier = new $report.openHier(data, this.tabs);
    this.hier.add(this.tabs);

    this.log = new $report.openLog(data, this.tabs);
    this.log.add(this.tabs);

  }

})($report);

