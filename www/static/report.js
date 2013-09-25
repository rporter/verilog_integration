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
  $report.data = function(){
    var data;
    return function(){
      if (data === undefined) {
        $report.report().data('options', {});
        data = $report.report().data('options');
      }
      if (!arguments) return data;
      var key = arguments[0];
      if (data.hasOwnProperty(key)) return data[key];
      if (arguments.length > 1) return data[key] = arguments[1];
      return data[key] = Object();
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

  $report.formatTabs = function(tabs, onempty) {
    function hijax(panel) { 
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
    function tabIndex(it) {
      return $(it).parents('li:first').prevAll('li').length;
    }
    tabs.tabs({
      load : function(tab, ui) { 
        hijax(ui.panel); 
      },
      tabTemplate: '<li><a href="#{href}">#{label}</a><a href="#" class="icon"><span class="ui-icon ui-icon-close"></span><span class="ui-icon ui-icon-refresh"></span></a></li>'
    });
    // close icon: removing the tab on click
    tabs.tabs().delegate("> ul span.ui-icon-close", "click", function() {
      tabs.tabs("remove", tabIndex(this));
      if (tabs.tabs('length') === 0) {
        // no tabs left; remove 
        tabs.tabs('destroy');
        if (onempty instanceof Function) {
          onempty();
        }
      } else {
        tabs.tabs("refresh");
      }
    });
    tabs.tabs().delegate("> ul span.ui-icon-refresh", "click", function() {
      tabs.tabs("load", tabIndex(this));
    });
  };

  $report.testJSON = function(url, data, anchor, order) {
    anchor = anchor || $report.tabs();
    var self = this;

    this.url = url;
    this.order = order || 'down';
    this.options = $report.data(url, {view:20, view_coverage:false});

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

    var coverage_cls = function (log) {
      if (!log.hasOwnProperty('coverage')) return 'unknown';
      if (log.goal && log.coverage) return 'both';
      if (log.goal)                 return 'goal';
      if (log.coverage)             return 'cvg';
      if (log.master)               return 'master'; // expected coverage
      return 'none';
    }

    this.render = function(available) {
      var container = $('<div><table class="display"></table></div>');
      self.container = container;
      $('table', container).dataTable({
        "bJQueryUI": true,
        "bPaginate": self.url === undefined,
        "bFilter": false,
        "bInfo": false,
        "aaData" : this.rows(),
        "aoColumns": this.cols(),
        "aoColumnDefs": [
          {
            "aTargets": [this.cols().length-1], // last col
            "fnCreatedCell": function(nTd, sData, oData, iRow, iCol) {
              $(nTd).addClass(sData);
            },
          }
        ],
        "aaSorting": [[0, "desc"]],
        "iDisplayLength": available || self.options.view,
        "fnCreatedRow": function(nRow, aData, iDisplayIndex) {
          var cvg = $('td:nth(8)', nRow).addClass('cvg').addClass('cvg-'+aData[8]);
          $(cvg).bind('show.example', function(event) {
            $.ajax({
              url : '/cvr/'+aData[0],
              dataType : 'json',
              success : function(json) {
                var result = coverage_cls(json);
                $(cvg).text(result).addClass('cvg-'+result);
                $(cvg).unbind('show.example'); // event.name // no need to do again
                $(nRow).data('coverage', json);
              },
              error : function(xhr, status, index) {
                var result = json.length?coverage_cls(json):'error';
                $(cvg).text('error').addClass('cvg-error');
                $(cvg).unbind('show.example'); // event.name // no need to do again
                console.log(xhr, status, index);
              }
            });
          });
          $(nRow).bind('click.example', {log_id : aData[0], children : aData[9], anchor : anchor},
            function(event) {
              var log;
              if (event.data.children) {
                // this will be a tab-within-tab
                log = new $report.openRegr(event.data);
              } else {
                // place report log in new tab
                log = new $report.openLog(event.data);
              }
              log.add(anchor);
            }
          );
        }
      });

      self.coverage = $('th:nth-child(9), td.cvg', container);
      if (self.options.view_coverage) {
        self.coverage.trigger('show.example');
      } else {
        self.coverage.hide();
      }
      if (self.url !== undefined) {
        var control = $('<div class="ui-corner-all control"></div>').prependTo(container);
        var lenctrl = $('<div class="length"><div>Fetch <select>'+
   	    '<option value="20">20</option>'+
   	    '<option value="50">50</option>'+
   	    '<option value="100">100</option>'+
   	    '</select> records</div></div>').appendTo(control);
        $('option[value='+self.options.view+']', lenctrl).attr('selected', 1);
        $('<input type="checkbox"/>').change(function() {
          self.options.view_coverage = $(this).is(':checked');
          if (self.options.view_coverage) {
            self.coverage.show().trigger('show.example');
          } else {
            self.coverage.hide();
          }
        }).appendTo(lenctrl).attr('checked', self.options.view_coverage).wrap('<div>Show Coverage</div>');
        var navigation = $('<div class="navigation"></div>');
        $('<span class="ui-icon ui-icon-seek-first"></span>').attr('title', 'first').appendTo(navigation);
        $('<span class="ui-icon ui-icon-seek-prev"></span>').attr('title', 'previous').appendTo(navigation);
        $('<span class="ui-icon ui-icon-seek-next"></span>').attr('title', 'next').appendTo(navigation);
        $('<span class="ui-icon ui-icon-seek-end"></span>').attr('title', 'last').appendTo(navigation);
        navigation.clone().addClass('left').prependTo(control);
        navigation.clone().addClass('right').appendTo(control);
        control.clone().appendTo(container);
        $('select', container).bind('change.example', self.select);
        $('span.ui-icon-seek-first', container).bind('click.example', self.first);
        $('span.ui-icon-seek-prev',  container).bind('click.example', self.prev);
        $('span.ui-icon-seek-next',  container).bind('click.example', self.next);
        $('span.ui-icon-seek-end',   container).bind('click.example', self.end);
      }
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
	{ "sTitle": "coverage" },
	{ "sTitle": "children" },
	{ "sTitle": "status" },
      ];
    };

    this.rows = function() {
      function popup(attr) {
          return '<abbr title="'+attr.msg.replace('"', '&quot;')+'">'+attr.count+'</abbr>';
      }
      return data.map(function(log){
        return [log.log.log_id, log.log.user, log.log.description, log.get('FATAL', popup), log.get('INTERNAL', popup), log.get('ERROR', popup), log.get('WARNING', popup), log.status.reason, coverage_cls(log.log), log.log.children, log.status.status];
      });
    };

    this.update = function() {
      var url = self.url + '/' + self.options.view;
      if (self.id !== undefined) {
        url += '/' + self.id;
      }
      if (self.order !== undefined) {
        url += '/' + self.order;
      }
      $.ajax({
        url : url,
        dataType : 'json',
        success : function(json) {
          if (json.length) {
            self.container.replaceWith((new $report.testJSON(self.url, json, anchor, self.order)).render(json.length));
          } else {
            alert('no more data');
            self.id = undefined;
          }
        },
        error : function(xhr, status, index) {
          console.log(xhr, status, index);
        }
      });
    }

    this.select = function() {
      var lenctrl = $(this).val();
      if (lenctrl != self.options.view) {
        self.id = data[data.length-1].log.log_id+1;
        self.order = 'down';
        self.options.view = lenctrl;
        self.update();
      }
    }

    this.first = function() {
      self.id = undefined;
      self.order = 'down';
      self.update()
    }

    this.next = function() {
      self.id = data[0].log.log_id;
      self.order = 'down';
      self.update()
    }

    this.prev = function() {
      self.id = data[data.length-1].log.log_id;
      self.order = 'up';
      self.update()
    }

    this.end = function() {
      self.id = undefined;
      self.order = 'up';
      self.update()
    }

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
      var show = $('<p class="show">Show<span class="ui-icon ui-icon-carat-1-s"></span></p>').appendTo(widget);
      var menu = $($('#menu').text()).appendTo(show).menu();
      show.bind('mouseenter.example', function() {menu.show();});
      menu.bind('mouseleave.example', function() {menu.hide();});

      var time = $('#time', menu);
      $('#hide', time).bind('click.example', function () {
        if ($('#hide span.ui-icon-check', time).hasClass('uncheck')) {
          $('span.ui-icon-check', time).addClass('uncheck');
          $('#hide span.ui-icon-check', time).removeClass('uncheck');
          $('time', self.div).hide();
	}
        menu.hide();
      });
      $('#rel', time).bind('click.example', function () {
        if ($('#rel span.ui-icon-check', time).hasClass('uncheck')) {
          $('span.ui-icon-check', time).addClass('uncheck');
          $('#rel span.ui-icon-check', time).removeClass('uncheck');
          $('time.abs', self.div).hide();
          $('time.rel', self.div).show();
 	}
        menu.hide();
      });
      $('#abs', time).bind('click.example', function () {
        if ($('#abs span.ui-icon-check', time).hasClass('uncheck')) {
          $('span.ui-icon-check', time).addClass('uncheck');
          $('#abs span.ui-icon-check', time).removeClass('uncheck');
          $('time.rel', self.div).hide();
          $('time.abs', self.div).show();
 	}
        menu.hide();
      });

      var ident = $('#ident', menu).bind('click.example', function () {
        $('#ident span.ui-icon-check', menu).toggleClass('uncheck');
        $('ident', self.div).toggle();
        menu.hide();
      });
      if (has_ident(self.json)) {
        ident.trigger('click');
      } else {
        $('a', ident).prop('title', 'there are no given idents');
        ident.addClass('ui-state-disabled');
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
            // place ellipsis in middle of list
            return ((nodes.length > 11)?Array.prototype.concat(nodes.slice(0,6), nodes.slice(-5)):nodes).map(
              function(it, idx){
                return {
                  "title"    : (idx==5 && nodes.length > 11)?'...':$report.levels.severity(parseInt($(it).attr('level'))),
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
        self.json = data.map(function(msg){msg.seconds = msg.date - data[0].date; return msg});
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
    this.explorer = $('<div class="explorer">');
    this.children = $('<div class="children">');

    // summary object
    this.summary = function() {
      var self = this;
      this.pass = 0;
      this.fail = 0;
      this.other = 0;
      this.total = function() {
        return self.pass + self.fail + self.other;
      }
      this.add = function(other) {
        if (other.status === 'PASS') {
          self.pass += 1;
        } else if (other.status === 'FAIL') {
          self.fail += 1;
        } else {
          self.other += 1;
        }
      }
      this.acc = function(other) {
        self.pass += other.pass;
        self.fail += other.fail;
        self.other += other.other;
      }
      this.html = function() {
        var result = '<result>';
        if (self.pass) result += ' <pass>'+self.pass+'</pass>';
        if (self.fail) result += ' <fail>'+self.fail+'</fail>';
        if (self.other) result += ' <other>'+self.other+'</other>';
        result += '</result>';
        return result;
      }
    };

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
    // depth first summary generation
    this.summarise = function summarise(tree) {
      tree.status.summary = new self.summary();
      tree.children.forEach(function(node){
        if (node.children) {
          self.summarise(node);
          tree.status.summary.acc(node.status.summary);
        }
        tree.status.summary.add(node.status);
      });
    }

    this.flatten = function flatten(json) {
      return json.concat(json.reduce(function(p,c){return p.concat(flatten(c.children));}, Array()));
    }

    this.find = function (log_id) {
      for (o in self.json) if (self.json[o].log.log_id == log_id) return self.json[o];
    }

    this.add = function(tabs) {
      tabs.tabs('add', '#'+self.id, data.log_id+' hier');
    };

    this.table = function(log_id) {
      self.children.html((new $report.testJSON(undefined, self.flatten([self.find(log_id),]), anchor)).render());
    };

    this.pane = function() {
      function hier(json, flat) {
        flat = flat || false;
        return json.map(function(it){return {title : '<div><span class="' + it.status.status + ' ' + ((it.status.status=='PASS')?'ui-icon-check':'ui-icon-close') + ' ui-icon"></span>&nbsp;' + it.log.description + '(' + it.log.log_id + ')' + ((it.status.summary===undefined)?'':it.status.summary.html()) + '</div>' , isFolder : it.children.length, key : it.log.log_id, children : flat?[]:hier(it.children || [], flat)}});
      }
      var tree = $('<div>').dynatree({
        children : [
            {title : "ALL", isFolder : true, key : null, children : hier(self.json, true)},
          hier(self.tree)[0]
        ],
        onExpand: function(flag, node) {
          if (flag) {
            self.table(node.data.key);
	  }
        },
        onActivate: function(node) {
          var create = node.data.children.length?$report.openRegr:$report.openLog;
          // this will be a tab-within-tab
          (new create({log_id : node.data.key, hier : [self.find(node.data.key),], anchor : anchor})).add(anchor);
        },
      });
      this.explorer.append(tree);
    }

    this.div.appendTo(anchor);
    this.div.append(this.explorer, this.children);
    if (data.hasOwnProperty('hier')) {
      self.tree = data.hier;
      self.json = self.flatten(self.tree);
      self.pane();
    } else {
      $.ajax({
        url : 'rgr/'+data.log_id,
        dataType : 'json',
        success : function(data) {
          self.json = data;
          self.tree = self.build(null);
          self.summarise(self.tree[0]);
          self.pane();
        },
        error : function(xhr, status, index) {
          console.log(xhr, status, index);
        }
      });
    }
  }

  $report.openRegr = function(data){
    var self = this;
    this.id  = $report.tab_id();
    this.div = $('<div>', {id : this.id}).append('<ul>');
    this.add = function(tabs) {
      self.parent = tabs;
      tabs.tabs('add', '#'+self.id, data.log_id+' regr');
    };
    this.close = function() {
      var index = $('li a[href="#'+self.id+'"]', self.parent).parent().index(); 
      self.parent.tabs("remove", index);
    };

    this.div.appendTo(data.anchor);
    this.tabs = this.div.tabs();
    $report.formatTabs(this.tabs, this.close);

    this.hier = new $report.openHier(data, this.tabs);
    this.hier.add(this.tabs);

    this.log = new $report.openLog(data, this.tabs);
    this.log.add(this.tabs);
    console.log(this.tabs);
  }

})($report);

