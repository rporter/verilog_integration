// Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

if (typeof String.prototype.startsWith != 'function') {
  String.prototype.startsWith = function (str){
    return this.slice(0, str.length) == str;
  };
}

// http://stackoverflow.com/questions/8786417/how-to-use-underscore-js-to-produce-a-flatten-result
// EXCEPT : here we stop when we see a leaf Array ------------------------>vvvvvvvvvvvvvvvvvvvvvvvvvv
_.mixin({crush: function(l, s, r) {return _.isObject(l)? (r = function(l) {if (_.isArray(l)) return l;return _.isObject(l)? _.flatten(_.map(l, s? _.identity:r)):l;})(l):[];}});

// http://www.yelotofu.com/2008/08/jquery-outerhtml/
jQuery.fn.outerHTML = function(s) {
    return s
        ? this.before(s).remove()
        : jQuery("<p>").append(this.eq(0).clone()).html();
};

$report = function(){
};

(function($report) {

  var coverage_cls = function (log) {
    if (!log.hasOwnProperty('coverage')) return 'unknown';
    if (log.goal && log.coverage) return 'both';
    if (log.goal)                 return 'goal';
    if (log.coverage)             return 'cvg';
    if (log.master)               return 'master'; // expected coverage
    return 'none';
  }

  $report.levels = {
    IGNORE      : 0,
    INT_DEBUG   : 1,
    DEBUG       : 2,
    INFORMATION : 3,
    NOTE        : 4,
    SUCCESS     : 5,
    WARNING     : 6,
    ERROR       : 7,
    INTERNAL    : 8,
    FATAL       : 9,
    _SIZE       : 10,
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
  $report.fit = function(obj, overflow) {
    var adjust  = true;
    var padding = parseInt($(obj).parents('div.ui-tabs-panel:first').css('padding-top'));
    if (isNaN(padding)) padding = 0;
    var fn      = function() {
      $(obj).height($(window).height() - $(obj).offset().top - padding);
    };
    var schedule = function(height) {
      if (!jQuery.contains(document.documentElement, obj[0])) {
        $report.fit.callbacks().remove(fn);
      } else {
        adjust = true;
        fn();
      }
    }
    $(obj).scroll(function() {
      if (adjust) {
        fn();
        adjust = false;
      }
    });
    if (overflow !== false) {
      obj.css('overflow-y', 'auto');
    }
    fn();
    $report.fit.callbacks().add(schedule);
  }
  $report.fit.callbacks = function() {
    if ($report.fit._callbacks === undefined) {
      $report.fit._callbacks = $.Callbacks();
      $(window).resize(function(){ $report.fit._callbacks.fire(); });
    }
    return $report.fit._callbacks;
  }

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
      panelTemplate: '<div class="tab"></div>',
      tabTemplate: '<li><span><a href="#{href}">#{label}</a><a href="#" class="icon"><span class="ui-icon ui-icon-close"></span><span class="ui-icon ui-icon-refresh"></span></a></span></li>'
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

    this.url = url && url.replace(/\/\d.*$/,'');
    this.type = this.url && this.url.split('/').pop()
    this.order = order || 'down';
    this.options = $report.data(this.url, {view:20, view_coverage:false});
    this.container = $('<div><table class="report"></table></div>');

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

    this.render = function(available) {
      var table = $('table', self.container).dataTable({
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
          // hoist into row tooltip
          $('td a[title]', nRow).each(function(){
            var it = $(this);
            it.parent().attr('title', it.attr('title')).tooltip().text(it.text());
          });
          $('td:first', nRow).attr('title', '').tooltip({
            content: function() {
              var log = data[iDisplayIndex].log,
                  table = ['log_id', 'activity', 'block', 'version'].reduce(function(l,it){if (log[it]===null) return l; return l+'<tr><td>'+it+'</td><td>'+log[it]+'</td></tr>'}, '');
              return $('<table>').append(table);
            }
          });
          $(nRow).bind('show.example', function(event){
            var cvg = $('td.cvg', nRow).addClass('cvg-'+aData[11]);
            $report.testJSON.get_cvg(cvg, nRow, data[iDisplayIndex].log.log_id)(event);
          });
          $(nRow).bind('click.example', {log_id : data[iDisplayIndex].log.log_id, name : $(aData[2]).text(), status : data[iDisplayIndex].status, log : data[iDisplayIndex].log, anchor : anchor},
            function(event) {
              var log;
              if (event.data.log.children) {
                if ($(event.target).next().length) {
                  // this will be a tab-within-tab
                  log = new $report.openRegr(event.data, nRow);
                } else {
                  log = new $report.openAutoRegr(data[iDisplayIndex].log.log_id, anchor);
                }
              } else {
                // place report log in new tab
                log = new $report.openLog(event.data, undefined, nRow);
              }
              log.add(anchor);
            }
          );
        }
      });

      var rows = $('tbody tr', self.container);
      if (self.options.view_coverage) {
        rows.trigger('show.example');
      } else {
        table.css('width', '100%')
      }

      if (self.url !== undefined) {
        var control = $('<div class="ui-corner-all control"></div>').prependTo(self.container);
        var lenctrl = $('<div class="length"><div>Fetch <select>'+
   	    '<option value="20">20</option>'+
   	    '<option value="50">50</option>'+
   	    '<option value="100">100</option>'+
   	    '</select> records</div></div>').appendTo(control);
        $('option[value='+self.options.view+']', lenctrl).attr('selected', 1);
        $('<input type="checkbox"/>').appendTo(lenctrl).attr('checked', self.options.view_coverage).wrap('<div>Show Coverage</div>');
        var navigation = $('<div class="navigation"></div>');
        $('<span class="ui-icon ui-icon-seek-first"></span>').attr('title', 'first').appendTo(navigation);
        $('<span class="ui-icon ui-icon-seek-prev"></span>').attr('title', 'previous').appendTo(navigation);
        $('<span class="ui-icon ui-icon-seek-next"></span>').attr('title', 'next').appendTo(navigation);
        $('<span class="ui-icon ui-icon-seek-end"></span>').attr('title', 'last').appendTo(navigation);
        navigation.clone().addClass('left').prependTo(control);
        navigation.clone().addClass('right').appendTo(control);
        control.clone().appendTo(self.container);
        $('select', self.container).bind('change.example', self.select);
        $('span.ui-icon-seek-first', self.container).bind('click.example', self.first);
        $('span.ui-icon-seek-prev',  self.container).bind('click.example', self.prev);
        $('span.ui-icon-seek-next',  self.container).bind('click.example', self.next);
        $('span.ui-icon-seek-end',   self.container).bind('click.example', self.end);
        $('input', self.container).change(function() {
          self.options.view_coverage = $(this).is(':checked');
          $('input', self.container).attr('checked', self.options.view_coverage);
          if (self.options.view_coverage) {
            table.fnSetColumnVis(11, true);
            rows.trigger('show.example');
          } else {
            table.fnSetColumnVis(11, false);
          }
        });
      }
      $report.fit(self.container);
      return self.container;
    }

    this.cols = function() {
      return [
	{ "sTitle": "log id" },
	{ "sTitle": "user" },
	{ "sTitle": "description" },
	{ "sTitle": "start" },
	{ "sTitle": "stop" },
	{ "sTitle": "duration" },
	{ "sTitle": "fatals" },
	{ "sTitle": "internals" },
	{ "sTitle": "errors" },
	{ "sTitle": "warnings" },
	{ "sTitle": "message" },
	{ "sTitle": "coverage", "sClass" : "cvg", "bVisible" : self.options.view_coverage },
	{ "sTitle": "children", "bVisible" : self.type !== $report.testJSON.types.single },
	{ "sTitle": "status" },
      ];
    };

    this.rows = function() {
      function popup(attr) {
        return $('<a>', {title:attr.msg, text:attr.count}).outerHTML();
      }
      function date(time) {
        return $('<a>', {text: time.calendar(), title: time.format('ddd MMMM Do YYYY, HH:mm:ss')}).outerHTML();
      }
      function elapsed(time) {
        var duration = moment.duration(time);
        return $('<a>', {text: Math.floor(duration.asHours())+':'+moment(time).format("mm:ss"), title: duration.humanize()}).outerHTML();
      }
      return data.map(function(log){
        var start = moment(log.log.start*1000), stop = moment(log.log.stop*1000);
        return [log.log.log_id, log.log.user, $('<a>', {title:log.log.description, text:log.log.test || log.log.description}).outerHTML(), date(start), date(stop), elapsed(stop.diff(start)), log.get('FATAL', popup), log.get('INTERNAL', popup), log.get('ERROR', popup), log.get('WARNING', popup), log.status.reason, coverage_cls(log.log), $report.testJSON.child_status(log.log), log.status.status];
      });
    };

    this.genurl = function() {
      var url = self.url + '/' + self.options.view;
      if (self.id !== undefined) {
        url += '/' + self.id;
      }
      if (self.order !== undefined) {
        url += '/' + self.order;
      }
      return url;
    }
    this.update = function() {
      self.container.children().fadeTo('slow', 0.3);
      var img = $('<img>', {src: 'static/loading.gif', class: 'loading'});
      img.css({
        'margin-left' : -img.width()/2,
        'margin-top'  : -img.height()/2
      }).appendTo(this.container);
      $.ajax({
        url : self.genurl(),
        dataType : 'json',
        success : function(json) {
          if (json.length) {
            self.container.replaceWith((new $report.testJSON(self.url, json, anchor, self.order)).render(json.length));
            // horriblish hack
            $report.tabs('url', $report.tabs('option', 'active') , self.genurl());
          } else {
            img.remove();
            self.container.children().fadeTo('slow', 1);
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
        // if we freeze the view start, then we won't get new entries when reselecting the tab
        // self.id = data[data.length-1].log.log_id+1;
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
    console.log(this);
  };

  $report.testJSON.types = {single:'sngl', regression:'regr', all:'all'};

  $report.testJSON.child_status = function (log) {
    if (log.children === null) return '';
    result = String(log.children) + '<result>';
    if (log.passing) result += ' <pass>' + log.passing + '</pass>';
    var failing = log.children - log.passing;
    if (failing) result += ' <fail>' + failing + '</fail>';
    result += '</result>';
    return result;
  };

  $report.testJSON.get_cvg = function(cvg, nRow, log_id, onsuccess) {
    return function(event) {
      $.ajax({
        url : '/cvr/'+log_id,
        dataType : 'json',
        success : function(json) {
          var result = coverage_cls(json);
          if (cvg) {
            $(cvg).addClass('cvg-'+result).html('<a class="popup onhover">'+result+'<span title="'+result+'"><table class="report">' + Object.keys(json).reduce(function(p, c){return p + '<tr><td>'+c+'</td><td>'+json[c]+'</td></tr>'}, '') + '</table></span></a>');
            $(cvg).unbind(event.type+'.'+event.namespace); // no need to do again
          }
          if (nRow) {
            $(nRow).data('coverage', json);
          }
          if (onsuccess !== undefined) {
            onsuccess(json);
          }
        },
        error : function(xhr, status, index) {
          if (cvg) {
            $(cvg).text('error').addClass('cvg-error');
            $(cvg).unbind(event.type+'.'+event.namespace); // no need to do again
          }
          console.log(xhr, status, index);
        }
      });
    };
  };

  $report.openLog = function(data, anchor, node) {
    var self = this;
    this.id  = $report.tab_id();
    this.div  = $('<div/>', {class: "tab", id:self.id});
    this.log  = $('<div/>', {		   id:"log"}).appendTo(this.div);
    this.coverage = $(node).data('coverage');
    anchor = anchor || data.anchor;

    this.wrap = function() {
      // if we determine this has coverage we'll need to push log stuff into another tab
      // firstly remove scrolling behaviour of parent tab
      this.div.removeClass('tab');
      this.log.addClass('tab');
      this.div.prepend('<ul><li><a href="#log">Log</a></li><li><a href="#cvg">Coverage</a></li><span style="float:right; margin:0.5em">'+data.name+'</span></ul>');
      this.cvg = $('<div/>', {class: "cvg-pane", id:"cvg"}).appendTo(this.div);
      this.tabs = this.div.tabs();
      function url() {
        var url = 'cvg/' + data.log_id;
        if (self.coverage.master) url += '/' + self.coverage.master;
        else if (self.coverage.root) url += '/' + self.coverage.root;
        return url;
      }
      $.ajax({
        url : url(),
        dataType : 'json',
        success : function(cdata) {
          $coverage.coverage(self.cvg, data.log_id, cdata);
        },
        error : function(xhr, status, index) {
          console.log(xhr, status, index);
        }
      });
    }

    this.widget = function() {
      var widget = $('<div class="widget"/>').appendTo(self.log);
      var align  = function() {
        widget.animate({top:$(self.log).scrollTop()},{duration:100,queue:false});
      };
      $(self.log).scroll(align);
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
          $('time', self.log).hide();
	}
        menu.hide();
      });
      $('#rel', time).bind('click.example', function () {
        if ($('#rel span.ui-icon-check', time).hasClass('uncheck')) {
          $('span.ui-icon-check', time).addClass('uncheck');
          $('#rel span.ui-icon-check', time).removeClass('uncheck');
          $('time.abs', self.log).hide();
          $('time.rel', self.log).show();
 	}
        menu.hide();
      });
      $('#abs', time).bind('click.example', function () {
        if ($('#abs span.ui-icon-check', time).hasClass('uncheck')) {
          $('span.ui-icon-check', time).addClass('uncheck');
          $('#abs span.ui-icon-check', time).removeClass('uncheck');
          $('time.rel', self.log).hide();
          $('time.abs', self.log).show();
 	}
        menu.hide();
      });

      var ident = $('#ident', menu).bind('click.example', function () {
        $('#ident span.ui-icon-check', menu).toggleClass('uncheck');
        $('ident', self.log).toggle();
        menu.hide();
      });
      if (self.json.idents) {
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
        self.json.msgs.forEach(function(it){if((it.level >= ui.values[0]) && (it.level <= ui.values[1])){it.element.show()}else{it.element.hide()}})
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

      var msgIndex = $('<div/>').appendTo(widget);
      var collections = new Array();

      function toDyn(thing, titles, extra) {
        if (thing instanceof Array) {
          // array
          return ((thing.length > 11)?Array.prototype.concat(thing.slice(0,6), thing.slice(-5)):thing).map(function(it, idx){
            return _.extend({
              key      : it.idx.toString(),
              title    : (idx==5 && thing.length > 11)?'...':it[titles[0]],
              tooltip  : it.msg
            }, extra);
          });
        } else {
          // object
          return _.map(thing, function(val, key) {
            var children = toDyn(val, titles.slice(1));
            return {
              key      : 'col-' + (collections.push(val)-1),
              title    : key + ' <i>(' + _.size(val) + ')</i>',
              tooltip  : children[0].tooltip,
              children : children
            };
          });
        }
      };
      function decode(key) {
        if (self.json[key]) return _.crush(self.json[key]);
        if (key.startsWith('col')) return _.flatten(collections[key.slice(4)]);
        return [self.json.msgs[key]];
      }

      self.tree = msgIndex.dynatree({
        children : [
          {title : "Messages", isFolder : true, key : 'severities', children : toDyn(self.json.severities, [null, 'severity'], {hideCheckbox : true}).sort(function(a,b){return self.json.msgs[a.children[0].key].level > self.json.msgs[b.children[0].key].level;})},
          {title : "Idents",   isFolder : true, key : 'idents', children : toDyn(self.json.idents, [null, 'ident', 'subident'])},
        ],
        checkbox : true,
        selectMode : 3,
        onSelect: function(select, node) {
          decode(node.data.key).forEach(function(it){it.element.toggle(select)});
        },
        onActivate: function(node) {
          self.log.animate({scrollTop : decode(node.data.key)[0].element.offset().top - self.log.offset().top + self.log.scrollTop() - self.log.height()/2});
        },
        onRender : function(dtnode, nodeSpan) {
          $('a', dtnode.li).hover(
            function(){decode($.ui.dynatree.getNode(this).data.key).forEach(function(it){it.element.addClass('example-highlight')})},
            function(){decode($.ui.dynatree.getNode(this).data.key).forEach(function(it){it.element.removeClass('example-highlight')})}
          ).tooltip({
            open: function(event, ui) {
              var tooltip=$(this);
              setTimeout(function close(){tooltip.tooltip('close')}, 2000);
            }
          });
          align();
        }
      });
      self.tree.dynatree("getRoot").childList.forEach(function(it){it.select(true)});
    }

    this.add = function(tabs) {
      var href='#'+self.id;
      tabs.tabs('add', href, data.log_id+' log').find('a[href="'+href+'"]').parents('li:first').prop('title', data.name).tooltip({
        position: {
          my: "center bottom",
          at: "center top",
          using: function( position, feedback ) {
            $(this).css(position).addClass('example '+ data.status.status);
          }
        }
      });
    }

    function wrapif(cvg) {
      self.coverage = self.coverage || cvg; // update coverage if given
      if (coverage_cls(self.coverage) !== 'none') {
        self.wrap();
      }
    }

    this.div.appendTo(anchor);

    if (self.coverage === undefined) {
      // fetch coverage
      $report.testJSON.get_cvg($('td.cvg', node), node, data.log_id, wrapif)({type:'show', namespace:'example'});
    } else {
      wrapif();
    }

    $.ajax({
      url : 'msgs/'+data.log_id,
      dataType : 'json',
      success : function(data) {
        self.json = {msgs : data.sort(function(x, y){var d = x.date - y.date; if (d===0) return x.msg_id - y.msg_id; return d; }).map(function(msg){msg.seconds = msg.date - data[0].date; return msg})};
        self.json.idents = _.groupBy(self.json.msgs.filter(function(msg){return msg.ident}), function(msg){return msg.ident});
        _.each(self.json.idents, function(v,k,l){self.json.idents[k]=_.groupBy(v,function(m){return m.subident})});
        self.json.severities = _.groupBy(self.json.msgs, function(msg){return msg.severity});
        var length = self.json.msgs.length, index = 0;

        $report.fit(self.log);

        function insertMsg(msg, id) {
          msg.element = $('<code>', {class:msg.severity, level:msg.level, text:'(' + $report.openLog.justify(msg.severity)}).appendTo(self.log);
          msg.idx = index;
          msg.moment = new moment(msg.date*1000);
          $('<time>', {class:'abs', text:' '+msg.moment.format('HH:mm:ss')}).appendTo(msg.element);
          $('<time>', {class:'rel', text:' '+$report.openLog.justify(msg.seconds.toString(), 6)}).appendTo(msg.element);
          if (msg.ident) {
            msg.element.attr({ident:msg.ident, subident:msg.subident});
          }
          $('<ident>', {text:$report.openLog.justify(id, 10)}).appendTo(msg.element);
          msg.element.append(') ' + $report.openLog.msg(msg.msg));
          msg.element.attr('title', '').tooltip({
            content: function() {
              var out = '<code class="'+msg.severity+'">';
              if (msg.ident) out += '<p class="id">'+id+'</p>';
              out +=  '<p class="date">' + msg.moment.format('dddd MMMM Do YYYY, HH:mm:ss') + '</p>'
              if (msg.filename) out += '<p class="file">'+msg.filename+':'+msg.line+'</p>';
              out+='</code>';
              return out;
            },
            open: function( event, ui ) {
              var tooltip=$(this);
              setTimeout(function close() {tooltip.tooltip('close')}, 2000);
            }
          });
        }

        function iteration(){
          for (; index<length;) {
            var msg = self.json.msgs[index];
            insertMsg(msg, $report.openLog.genIdent(msg));
            if (index++ < length && index % 100 == 0) {
              setTimeout(iteration, 0); break;
            }
            if (index == length) {
              self.widget();
            }
          }
        }
        iteration();
      },
      error : function(xhr, status, index) {
        console.log(xhr, status, index);
      }
    });

  };

  $report.openLog.justify = function (c, l) {
    l = l || 12;
    return Array(l).join(' ').substr(c.length) + c;
  };
  $report.openLog.msg = function (m) {
    return m.replace(/>/g, '&gt;').replace(/</g, '&lt;');
  };
  $report.openLog.genIdent = function (msg) {
    return msg.ident?(msg.ident+'-'+msg.subident):'';
  };

  $report.openHier = function(data, anchor){
    var self = this;
    this.id  = $report.tab_id();
    this.div = $('<div>', {id : this.id});
    this.explorer = $('<div class="explorer">');
    this.children = $('<div class="children">');

    // add scrollbar if necessary
    $report.fit(this.explorer);

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
      var href='#'+self.id;
      tabs.tabs('add', href, data.log_id+' hier').find('a[href="'+href+'"]').parents('li:first').prop('title', data.name).tooltip({
        position: {
          my: "center bottom",
          at: "center top",
          using: function( position, feedback ) {
            $(this).css(position).addClass('example '+ data.status.status);
            $($report.testJSON.child_status(data.log)).appendTo($('div', this));
          }
        }
      });
    };

    this.table = function(log_id) {
      self.children.html((new $report.testJSON(undefined, self.flatten([self.find(log_id),]), anchor)).render());
    };

    this.pane = function() {
      function name(log) {
        if (log.test) return '<abbr title="'+log.description+'">'+log.test+'</span>'
        return log.description;
      }
      function hier(json, flat) {
        flat = flat || false;
        return json.map(function(it){return {title : '<div><span class="' + it.status.status + ' ' + ((it.status.status=='PASS')?'ui-icon-check':'ui-icon-close') + ' ui-icon"></span>&nbsp;' + name(it.log) + '(' + it.log.log_id + ')' + ((it.status.summary===undefined)?'':it.status.summary.html()) + '</div>' , isFolder : it.children.length, key : it.log.log_id, children : flat?[]:hier(it.children || [], flat)}});
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
          var json = self.find(node.data.key);
          (new create({log_id : node.data.key, name : json.log.test || json.log.description || 'none given', status : json.status, log : json.log, hier : [json,], anchor : anchor})).add(anchor);
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
        success : function(json) {
          self.json = json;
          self.tree = self.build(null);
          self.summarise(self.tree[0]);
          self.pane();
          self.triage = new $report.openTriage(data, anchor, json);
          self.triage.add(anchor);
        },
        error : function(xhr, status, index) {
          console.log(xhr, status, index);
        }
      });
    }
  }

  $report.openTriage = function(data, anchor, json) {
    var self = this;
    this.id  = $report.tab_id();
    this.div = $('<div>', {id: this.id});

    this.add = function(tabs, event) {
      var href='#'+self.id;
      tabs.tabs('add', href, data.log_id+' triage');
      if (event) {
        tabs.tabs({activate : event});
      }
    };

    this.div.appendTo(anchor);
    this.div.html('<div><table class="report"><thead title="click to hide PASSes"><tr><th rowspan=2>severity</th><th rowspan=2>filename</th><th rowspan=2>line</th><th rowspan=2>ident</th><th rowspan=2>subident</th><th rowspan=2>message</th><th rowspan=2>description</th><th rowspan=2>testname</th><th rowspan=2>log_id</th><th colspan="2">status</th></tr><tr><th>message</th><th>status</th></th></thead><tbody/></table></div>');
    $report.fit($('div', this.div));
    var tbody = $('tbody', this.div);

    tbody.tooltip({
      items : 'td',
      content : function() {
        var tests = $(this).attr('rowspan');
        if (tests > 1) return tests + ' tests';
      }
    });

    function ifnull(value, repl) {
      return (value === null)?repl:value;
    }

    this.build = function build(tests, depth) {
      depth = depth || 0;
      var name = $report.openTriage.attributes[depth];
      var items = _.groupBy(tests, function(test){return ifnull(test.log[name], '-')});
      _.each(_.sortBy(_.pairs(items), function(it){if (depth) return -it[1].length; return -it[1][0].log.level}), function(it) {
        var tests = it[1],
            attr = it[0], 
            row = $('tr:last', tbody);
        // if the last cell of the last row does not have previous attribute make new row
        if (!$('td:last', row).hasClass($report.openTriage.attributes[depth-1])) {
          row = $('<tr>').appendTo(tbody);
        }
        $('<td>', {class:name, rowspan : tests.length, text : name=='level'?tests[0].log.severity:attr}).appendTo(row);
        if (depth == $report.openTriage.attributes.length-1) {
          tests.forEach(function(test, idx) {
            if (idx > 0) row = $('<tr>').appendTo(tbody);
            $('<td>', {text : test.log.log_id}).appendTo(row);
            $('<td>', {text : test.status.reason}).appendTo(row);
            $('<td>', {text : test.status.status, class : test.status.status}).appendTo(row);
            row.bind('click.example',
              function() {
                (new $report.openLog({log_id : test.log.log_id, name : test.log.description, status : test.status}, anchor, row)).add(anchor);
              }
            );
          });
        } else {
          build(tests, depth+1);
        }
      });
    }

    this.update = function(json) {
      self.div.fadeTo(0.3);
      $('tr', tbody).remove();
      self.build(json);
      self.div.fadeTo(1);
    }

    this.build(json);
    $('thead', this.div).bind('click.example', function(){$('tr:has(td.PASS)', this.div).toggle()});
  }
  $report.openTriage.attributes = ['level', 'filename', 'line' , 'ident', 'subident', 'msg', 'description', 'testname'];

  $report.openRegr = function(data, node) {
    var self = this;
    this.id  = $report.tab_id();
    this.div = $('<div>', {id : this.id}).append('<ul>');
    this.coverage = $(node).data('coverage');

    this.add = function(tabs) {
      self.parent = tabs;
      var href='#'+self.id;
      tabs.tabs('add', href, data.log_id+' regr').find('a[href="'+href+'"]').parents('li:first').prop('title', data.name).prop('title', data.name).tooltip({
        position: {
          my: "center bottom",
          at: "center top",
          using: function( position, feedback ) {
            $(this).css(position).addClass('example '+ data.status.status);
            $($report.testJSON.child_status(data.log)).appendTo($('div', this));
          }
        }
      });
    };
    this.close = function() {
      var tab = $('li a[href="#'+self.id+'"]', self.parent).parent().parent();
      var index = tab.prevAll('li').length;
      self.parent.tabs("remove", index);
    };

    this.div.appendTo(data.anchor);
    this.tabs = this.div.tabs();
    $report.formatTabs(this.tabs, this.close);
    $('ul', this.tabs).append('<span style="float:right; margin:0.5em">'+data.name+'</span>');

    this.hier = new $report.openHier(data, this.tabs);
    this.hier.add(this.tabs);

    this.log = new $report.openLog(data, this.tabs);
    this.log.add(this.tabs);

    function addcvg(cvg) {
      self.coverage = self.coverage || cvg; // update coverage if given
      if (coverage_cls(self.coverage) !== 'none') {
        self.cvg = $('<div/>', {class: 'tab cvg-pane', id:'cvg-'+self.id}).appendTo(self.div);
        self.tabs.tabs('add', '#cvg-'+self.id, data.log_id+' cumulative coverage');
        function url() {
          var url = 'cvg/' + data.log_id;
          if (self.coverage.master) url += '/' + self.coverage.master;
          else if (self.coverage.root) url += '/' + self.coverage.root;
          return url + '/cumulative';
        }
        $.ajax({
          url : url(),
          dataType : 'json',
          success : function(cdata) {
            $coverage.coverage(self.cvg, data.log_id, cdata);
          },
          error : function(xhr, status, index) {
            console.log(xhr, status, index);
          }
        });
      }
    }

    if (self.coverage === undefined) {
      // fetch coverage
      $report.testJSON.get_cvg($('td.cvg', node), node, data.log_id, addcvg)({type:'show', namespace:'example'});
    } else {
      addcvg();
    }
    console.log(this);
  }

  $report.openAutoRegr = function(log_id, anchor) {
    var self = this;
    this.id  = $report.tab_id();
    this.div = $('<div/>', {id:self.id}).append('<ul><li><a href="#results">Results</a></li></ul>');
    this.log = $('<div/>', {class: "tab", id:"results"}).appendTo(this.div);
    this.url = '/irgr/' + log_id;

    var table = $('<table class="report"><thead><tr><th>log id</th><th>description</th><th>start</th><th>stop</th><th>duration</th><th>internals</th><th>fatals</th><th>errors</th><th>warnings</th><th>message</th><th>status</th></th></tr></thead><tbody/></table>').appendTo(this.log);
    var tbody = $('tbody', table);

    function find(log_id) {
      return _.find(self.data, function(it){return it.log.log_id==log_id});
    }
    function replace(data) {
      for (log in self.data) {
        if (self.data[log].log.log_id == data.log.log_id) {
          self.data[log] = data;
          return;
        }
      }
    }
    function time(log) {
      var diff = log.log.stop.diff(log.log.start), duration = moment.duration(diff);
      return {duration : function(){return Math.floor(duration.asHours()) + ':' + moment(diff).format("mm:ss")}, humanize : function(){return duration.humanize()}};
    }
    tbody.tooltip({
      items : 'td',
      content : function() {
        var idx = $(this).prevAll().length, log = find($(this).parent().attr('log_id'));
        switch (idx) {
          case  0 : return $('<table>').append(['log_id', 'activity', 'block', 'version'].reduce(function(l, it){if (log.log[it]===null) return l; return l+'<tr><td>'+it+'</td><td>'+log.log[it]+'</td></tr>'}, ''));
          case  1 : return log.log.description;
          case  2 : return log.log.start.format('ddd MMMM Do YYYY, HH:mm:ss');
          case  3 : return log.log.stop.format('ddd MMMM Do YYYY, HH:mm:ss'); 
          case  4 : return time(log).humanize();
          case  9 : return;
          case 10 : return;
          default :
            return log.get(['INTERNAL', 'FATAL', 'ERROR', 'WARNING'][idx-3], 'msg');
        }
      }
    });

    function get(severity, attr) {
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
    function addRow(log) {
      var tr = $('<tr>', {log_id : log.log.log_id});
      $('<td>', {text: log.log.log_id}).appendTo(tr);
      $('<td>', {text: log.log.testname+'-'+log.log.seed}).appendTo(tr);
      $('<td>', {text: log.log.start.calendar()}).appendTo(tr);
      $('<td>', {text: log.log.stop.calendar()}).appendTo(tr);
      $('<td>', {text: time(log).duration()}).appendTo(tr);
      $('<td>', {text: log.get('INTERNAL', 'count')}).appendTo(tr);
      $('<td>', {text: log.get('FATAL', 'count')}).appendTo(tr);
      $('<td>', {text: log.get('ERROR', 'count')}).appendTo(tr);
      $('<td>', {text: log.get('WARNING', 'count')}).appendTo(tr);
      $('<td>', {text: log.status.reason}).appendTo(tr);
      $('<td>', {class: log.log.status === null?'RUNNING':log.status.status, text: log.status.status}).appendTo(tr);
      return tr;
    }

    // data calls
    this.initial = function(data) {
      self.data = data;
      data.forEach(function(it){addRow(it).prependTo(tbody)});
      self.triage = new $report.openTriage({log_id : log_id}, self.tabs, self.data);
      self.triage.add(self.tabs, function(event, ui) {
        if (ui.newTab.attr('aria-controls') == self.triage.id) {
          self.triage.update(self.data);
        }
      });
    }
    this.addition = function(data) {
      var add = $();
      data.forEach(function(it){
        add=add.add(addRow(it).prependTo(tbody));
        self.data.push(it);
      });
      $('td', add).wrapInner('<div style="display: block;"/>');
      $('div', add).hide().slideDown();
    }
    this.update = function(data) {
      var add = $(), rm = $();
      data.forEach(function(it){
        var repl = $('tr[log_id='+it.log.log_id+']', tbody);
        add=add.add(addRow(it).insertBefore(repl));
        rm=rm.add(repl);
        replace(it);
      });
      $('td', add).wrapInner('<div style="display: block;"/>');
      $('div', add).hide().slideDown();
      $('td', rm).wrapInner('<div style="display: block;"/>');
      $('div', rm).slideUp(
        function() {tr=$(this);
          $(this).parents('tr').remove();
        }
      );
    }
    this.final = function(data) {
      this.update(_.filter(data, function(it){
        return !_.isEqual(find(it.log.log_id), it);
      }));
    }
    this.static = function(data) {
    }
    this.eof = function(data) {
    }

    this.oboe = oboe(self.url).node({
      '!.[*].*': function(node, path) {
        for (log in node) {
          node[log].get = get;
          node[log].log.start = moment(node[log].log.start*1000);
          node[log].log.stop  = moment(node[log].log.stop *1000);
        }
        self[path[1]](node);
        $report.fit(self.log);
      }
    }).done(function(i){
      $('td.RUNNING', tbody).removeClass('RUNNING').addClass('FAIL');
    }).fail(function(e){
      console.error(e.thrown.stack);
    });

    this.add = function(tabs) {
      self.parent = tabs;
      var href='#'+self.id;
      tabs.tabs('add', href, log_id+' regr').tabs({
        remove: function(event, ui) {
          if (ui.tab.hash == href) {
            self.oboe.abort();
          }
        }
      });
    }
    this.div.appendTo(anchor);
    this.tabs = this.div.tabs();
    console.log(this);
  }

})($report);

