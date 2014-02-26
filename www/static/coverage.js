// Copyright (c) 2013 Rich Porter - see LICENSE for further details

// J Resig says this is okay (add methods to built in prototypes, that is)

// Function to get the Max value in Array
Array.max = function( array ){
    return Math.max.apply( Math, array );
};

// Function to get the Min value in Array
Array.min = function( array ){
   return Math.min.apply( Math, array );
};

Array.has = function( array, fn ) {
   for ( i=0 ; i<array.length ; i++) {
      if (fn(array[i]) === true) return true;
   }
   return false;
};

Array.findIndex = function (arr, predicate, thisValue) {
    if (typeof predicate !== 'function') {
        throw new TypeError();
    }
    for(var i=0; i < arr.length; i++) {
        if (i in arr) {  // skip holes
            var elem = arr[i];
            if (predicate.call(thisValue, elem, i, arr)) {
                return i;
            }
        }
    }
    return -1;
}
Array.find = function (arr, predicate, thisValue) {
    if (typeof predicate !== 'function') {
        throw new TypeError();
    }
    for(var i=0; i < arr.length; i++) {
        if (i in arr) {  // skip holes
            var elem = arr[i];
            if (predicate.call(thisValue, elem, i, arr)) {
                return elem;
            }
        }
    }
    return undefined;
}

$coverage = function(){};

(function($coverage) {

  $coverage.chart_id = function(root) {
    var id = 0;
    return function() {
      id+=1;
      return root+id;
    };
  }('chart-');

  $coverage.coverageSummaryTable = function coverageSummaryTable(tree, where, title, coverpoint) {
    var self    = this;
    function _default(it) {
      return it || '<i>not given</i>';
    }

    function data() {
      return coverpoint.children.map(function(it){return [_default(it.hierarchy), _default(it.description), it.coverage.hits, it.coverage.goal, it.coverage.coverage.toFixed(2)]});
    }

    this.build = function() {
      where.html($('<h3/>', {html: title}));
      $('<table/>').appendTo(where).dataTable({
        "bJQueryUI": true,
        "bInfo": false,
        "bFilter": false,
        "aoColumns": [
  	  { "sTitle": "name" },
  	  { "sTitle": "description" },
	  { "sTitle": "hits" },
	  { "sTitle": "goal" },
	  { "sTitle": "coverage %" }
        ],
        "aaData": data(),
        "aaSorting" : [],
        "bLengthChange" : false,
        "bPaginate" : false,
        "iDisplayLength": -1,
        "sScrollY" : 'auto',
        "fnCreatedRow": function(nRow, aData, iDisplayIndex) {
          var point = coverpoint.children[iDisplayIndex];
          $(nRow).addClass(point.coverage.status);
          $('td:last', nRow).attr('title', point.coverage.description);
          $(nRow).bind('click.example',
            function(event) {
              tree.dynatree("getTree").getNodeByKey(String(point.id)).span.click();
            }
          );
        }
      }).wrap('<div class="table"/>');
      $report.fit($('div.table', where));
    }

    this.build();

    console.log(this);
  }

  $coverage.coverageTable = function coverageTable(log_id, where, title, coverpoint, options) {
    var matrix  = {table:'table', matrix:'matrix', graph:'graph'};
    var self    = this;
    var buckets = coverpoint.buckets;
    var axes    = $.extend(true, [], coverpoint.axes);
    var offset  = coverpoint.offset;
    var table;
    options = options || {};
    options = $.extend(options, {hide_hits : false, hide_illegal : false, hide_dont_care : false, matrix : matrix.table});

    function visible_axes() {
      return axes.reduce(function(sum, it, idx){
        if (it.visible !== false) {
          sum.push(it);
        }
        return sum;
      }, Array());
    }
    function invisible_axes() {
      return axes.reduce(function(sum, it, idx){
        if (it.visible === false) {
          sum.push(it);
        }
        return sum;
      }, Array());
    }
    function one_axis() {
      return visible_axes().length == 1;
    }
    function two_axes() {
      return visible_axes().length == 2;
    }
    function all_visible() {
      return visible_axes().length == axes.length;
    }

    function permsFromBucket(axes, bucket) {
      if (axes.length == 0) return ""; // terminal case
      var last = axes.slice(-1)[0];
      if (last.visible === false) {
        return permsFromBucket(axes.slice(0, -1), bucket);
      }
      return permsFromBucket(axes.slice(0, -1), Math.floor(bucket/last.values.length))+"<td>"+last.values[bucket % last.values.length]+"</td>";
    }

    function axisIdxs(bucket, axesSlice) {
      axesSlice = axesSlice || axes;
      if (axesSlice.length == 0) return []; // terminal case
      var last = axesSlice.slice(-1)[0];
      return axisIdxs(Math.floor(bucket/last.values.length), axesSlice.slice(0,-1)).concat([[bucket % last.values.length, last.values.length]]);
    }

    function bucketIdx(axisIdxs) {
      var cumul = 1;
      return axisIdxs.reduceRight(function(p, c, idx) {
        if (axes[idx].visible === false) return p;
        var result = p + c[0]*cumul;
        cumul *= c[1];
        return result;
      }, 0);
    }

    function scrollWheel(table) {
      table.bind('wheel mousewheel', function(event) {
        var oSettings = table.fnSettings();
        var delta = event.originalEvent.wheelDelta || event.originalEvent.deltaY;
        if (delta/120 > 0) {
          if (oSettings._iDisplayStart >= (oSettings.aoData.length - oSettings._iDisplayLength)) {
            return false;
          }
          oSettings.iInitDisplayStart = oSettings._iDisplayStart + 1;
        } else {
          if (oSettings._iDisplayStart < 1) {
            return false;
          }
          oSettings.iInitDisplayStart = oSettings._iDisplayStart - 1;
        }
        table.fnDraw();
        return false;
      });
    }

    function showDialog(event) {
      // create table of all hits in a dialog popup
      var container = $('<div><div><table/></div></div>').attr('title', title+'['+event.data.bucket_id+']').css("white-space", "nowrap");
      var table = $('table', container).dataTable({
        "bJQueryUI": true,
        "bFilter": false,
        "aoColumns": [
  	  { "sTitle": "log id" },
  	  { "sTitle": "test" },
	  { "sTitle": "hits" }
        ],
        "aaData" : event.data.coverage.map(function(hit){return [hit.log_id, '<span title="'+hit.description+'">'+hit.test+'</span>', hit.hits]}),
        "aaSorting": [[2, "desc"]], // sort hits descending
        "aLengthMenu": [[10, 25, 50, 100 , -1], [10, 25, 50, 100, "All"]],
        "iDisplayLength": 10,
        "fnCreatedRow": function(nRow, aData, iDisplayIndex) {
          $(nRow).addClass(coverageTable.classFromBucket([event.data.goal, aData[2]]));
          $(nRow).bind('click.example', {log_id : aData[0], anchor : where.parents('div.ui-tabs:first')},
            function(event) {
              var log = new $report.openLog(event.data, undefined, nRow);
              log.add(event.data.anchor);
            }
          );
        }
      });
      scrollWheel(table);
      container.dialog({width:"auto"});
    }

    function showBucket(node) {
      var bucket_id = parseInt(node.attr('bkt'));
      var bucket    = buckets[bucket_id];
      var goal      = bucket[0];
      var url       = '/bkt/' + log_id + '/';
      if (buckets.hasOwnProperty('aliases')) {
        url += buckets.aliases[bucket_id].map(function(bkt){return bkt+offset}).join(',');
      } else {
        url += (bucket_id + offset);
      }
      node.removeAttr('title');
      node.html(function(){
        return '<a class="popup">' + $(this).html() + '<span id="hits-' + bucket_id + '" title="hit details for ' + log_id + '/' + bucket_id + '"><h5 style="margin:0">goal : '+bucket[0]+'</h5></span></a>';
      });
      $.getJSON(url, function(data) {
        $('span', node).append(function() {
          if (data.length) {
            node.bind('click.coverage', {coverage:data, goal:goal, bucket_id:bucket_id}, showDialog);
            return $('<table/>', {
              class : 'bucket',
              html : '<tbody>'+data.slice(0,10).map(function(it){
                return '<tr class="'+coverageTable.classFromBucket([goal, it.hits])+'"><td>'+it.log_id+'</td><td>'+it.hits+'</td></tr>';
              })+'</tbody>'
            });
          } else {
            return $('<i/>', {html : 'no hits'});
          }
  	});
      });
      node.unbind('mouseenter.coverage'); // don't do again
    }

    function showAliases(node) {

      function permsFromBucket(axes, bucket, values) {
        if (axes.length == 0) return values; // terminal case
        values = values || [];
        var last = axes.slice(-1)[0];
        if (last.visible === false) {
          values.push(last.values[bucket % last.values.length]+"</td>");
        }
        return permsFromBucket(axes.slice(0, -1), Math.floor(bucket/last.values.length), values);
      }

      var bucket_id = parseInt(node.attr('bkt'));
      var bucket    = buckets[bucket_id];
      var goal      = bucket[0];
      var title     = 'alias details for ' + log_id + '/' + bucket_id;
      node.removeAttr('title');
      node.html(function(){
        return '<a class="popup">' + $(this).html() + '<span id="hits-' + bucket_id + '" title="'+title+'"><h5 style="margin-bottom:0.2em;margin-top:0;text-align: center">goal : '+bucket[0]+'</h5></span></a>';
      });
      if (!all_visible()) {
        var
          table = $('<table><thead><tr>' + invisible_axes().reduce(function(p, c){return p+'<th>'+c.name+'</th>'}, '') + '<th>goal</th><th>hits</th></tr></thead><tbody/></table>').appendTo($('span', node)),
          tbody = $('tbody', table);
        buckets.aliases[bucket_id].forEach(function(it){
          var bkt = coverpoint.buckets[it];
          $('<tr>'+permsFromBucket(axes, it).reduce(function(p, c){return p+'<td>'+c+'</td>'}, '')+'<td>'+bkt[0]+'</td><td>'+bkt[1]+'</td></tr>').addClass(coverageTable.classFromBucket(bkt)).appendTo(tbody);
        });
        node.bind('click.coverage', function() {
          var container = $('<div><div><table/></div></div>').attr('title', title).css("white-space", "nowrap");
          var table = $('table', container).dataTable({
            "bJQueryUI": true,
            "bFilter": false,
            "aoColumns": Array.prototype.concat([{ "sTitle": "bucket", "bVisible": true },], invisible_axes().map(function(it){return { "sTitle": it.name }}), [
              { "sTitle": "goal" },
              { "sTitle": "hits" }
            ]),
            "aaData" : buckets.aliases[bucket_id].map(function(it){return Array.prototype.concat([it,], permsFromBucket(axes, it), coverpoint.buckets[it])}),
            "aaSorting": [[0, "asc"]], // sort on bkt id
            "aLengthMenu": [[10, 25, 50, 100 , -1], [10, 25, 50, 100, "All"]],
            "iDisplayLength": 10,
            "fnCreatedRow": function(nRow, aData, iDisplayIndex) {
              $(nRow).addClass(coverageTable.classFromBucket(coverpoint.buckets[aData[0]]));
            }
          });
          scrollWheel(table);
          container.dialog({width:"auto"});
        });
      }
      node.unbind('mouseenter.coverage'); // don't do again
    }

    function updateVisible() {
      $('th.axis.selected', where).each(function(idx, node){
        axes[parseInt($(node).attr('idx'))].visible = false;
      });
    }
    function allVisible() {
      axes.map(function(it){it.visible = true});
    }

    function checkBuckets() {
      if (!Array.has(axes, function(it){return it.visible !== false})) {
        alert('Nothing visible!');
        return false;
      }
      return true;
    }

    function heat_bkt(values) {
      this.values = $.extend(true, [], values);

      this.findIndex = function(name) {
        return Array.findIndex(this.values, function(it){return it.testname == name});
      }
      this.find = function(name) {
        return Array.find(this.values, function(it){return it.testname == name});
      }
      this.hits = function(name) {
        return (this.find(name) || {hits:0}).hits;
      }
      this.add = function(other) {
        if (other === undefined) return;
        // add those with same test index copy those without
        other.values.forEach(function(value) {
          var idx = this.findIndex(value.testname);
          if (idx < 0) {
            // not found, copy this
            this.values.push($.extend({}, value));
          } else {
            // accumulate this to existing
            this.values[idx].hits += value.hits;
            this.values[idx].tests += value.tests;
          }
        }, this);
      }
    }
    heat_bkt.clone = function(other) {
      if (other) {
        return new heat_bkt(other.values);
      }
      return new heat_bkt();
    }


    function updateBuckets() {
      if (!checkBuckets()) {
        return false;
      }
      var has_heat_map = coverpoint.hasOwnProperty('heat_map');
      // reduce buckets
      buckets = [];
      buckets.aliases = [];
      if (has_heat_map) {
        buckets.heat_map = [];
      }
      for (var bucket=0; bucket<coverpoint.buckets.length; bucket++) {
        var idx = bucketIdx(axisIdxs(bucket));
        if (buckets[idx] === undefined) {
          buckets[idx] = coverpoint.buckets[bucket].slice(); // copy
          buckets.aliases[idx] = [bucket,];
          if (has_heat_map) {
            buckets.heat_map[idx] = heat_bkt.clone(coverpoint.heat_map.buckets[bucket]);
          }
        } else {
          // calculate goal
          if (coverpoint.buckets[bucket][0] > 0) {
            if (buckets[idx][0] < 0) {
              // previously marked as illegal, so now make hittable
              buckets[idx][0] = coverpoint.buckets[bucket][0];
            } else {
              buckets[idx][0] += coverpoint.buckets[bucket][0];
            }
          }
          // calculate hits
          // don't care if source bucket uninteresting, hence no qualification on goal
          buckets[idx][1] += coverpoint.buckets[bucket][1];
          // store alias list
          buckets.aliases[idx].push(bucket)
          // accumulate heat data
          if (has_heat_map) {
            buckets.heat_map[idx].add(coverpoint.heat_map.buckets[bucket]);
          }

        }

      }
      return true;
    }

    function resetBuckets() {
      buckets = coverpoint.buckets;
      delete buckets.aliases;
      delete buckets.heat_map;
    }

    function hideSelected() {
      updateVisible();
      if (!updateBuckets()) { 
        return;
      }
      self.build();
    }

    function nonSortableAxes() {
      var idx=1;
      return axes.reduce(function(p,c){
        if (c.visible !== false) {
          p[idx]={sorter:false};
          idx+=1;
        }
        return p;
      }, {});
    }

    function addMenu() {
      var cvg_point_menu = $($('#cvg-point-menu').text()).appendTo(where).menu().hide();
  
      cvg_point_menu.mouseup(function(){
        cvg_point_menu.hide();
      }).mouseleave(function(){
        cvg_point_menu.hide();
      });

      if (options.hide_hits) {
        $('#hide-hits span.ui-icon', cvg_point_menu).addClass('check');
      }
      if (options.hide_dont_care) {
        $('#hide-dontcare span.ui-icon', cvg_point_menu).addClass('check');
      }
      if (options.hide_illegal) {
        $('#hide-illegal span.ui-icon', cvg_point_menu).addClass('check');
      }
      if (two_axes()) {
        if (options.matrix == matrix.matrix ) {
          $('#matrix span.ui-icon', cvg_point_menu).addClass('check');
        }
        $('#graph', cvg_point_menu).addClass('grey');
      } else if (one_axis()) {
        if (options.matrix == matrix.graph ) {
          $('#graph span.ui-icon', cvg_point_menu).addClass('check');
        }
        $('#matrix', cvg_point_menu).addClass('grey');
      } else {
        options.matrix = options.table;
        $('#matrix, #graph', cvg_point_menu).addClass('grey');
      }
      if (coverpoint.cumulative === true) {
        if (coverpoint.hasOwnProperty('heat_map')) {
          $('#heat span.ui-icon', cvg_point_menu).addClass('check');
          if (options.heat_map !== true) {
            $('#heat', cvg_point_menu).addClass('grey');
          }
        }
      } else {
        $('#heat', cvg_point_menu).addClass('grey');
      }

      var elapsed, source;
      var th = $('th.axis', where).mousedown(function(event){
        event.preventDefault();
        source = $(this);
        elapsed = false;
        this.downTimer = setTimeout(function() {
          elapsed = true;
          if (source.hasClass('selected')) {
            $('#select span.ui-icon', cvg_point_menu).addClass('check');
            $('#unselect span.ui-icon', cvg_point_menu).removeClass('check');
          } else {
            $('#select span.ui-icon', cvg_point_menu).removeClass('check');
            $('#unselect span.ui-icon', cvg_point_menu).addClass('check');
          }
          if ($('#hide-dontcare span.ui-icon', cvg_point_menu).hasClass('check') &&
              $('#hide-illegal  span.ui-icon', cvg_point_menu).hasClass('check')) {
            $('#hide-both span.ui-icon', cvg_point_menu).addClass('check');
          } else {
            $('#hide-both span.ui-icon', cvg_point_menu).removeClass('check');
          }
          cvg_point_menu.show().position({
            my: "left top",
            of: event,
            collision : "flip"
          });
        }, 300);
      }).mouseup(function(e) {
        clearTimeout(this.downTimer);
        if (elapsed == false) {
          $(this).toggleClass('selected');
        } else {
          cvg_point_menu.hide();
        }
      });
      $('#select', cvg_point_menu).mouseup(function() {
        source.addClass('selected');
      })
      $('#unselect', cvg_point_menu).mouseup(function() {
        source.removeClass('selected');
      })
      $('#hide', cvg_point_menu).mouseup(function() {
        source.addClass('selected');
        hideSelected();
      })
      $('#hide-only', cvg_point_menu).mouseup(function() {
        th.removeClass('selected');
        source.addClass('selected');
        allVisible();
        hideSelected();
      })
      $('#hide-others', cvg_point_menu).mouseup(function() {
        th.addClass('selected');
        source.removeClass('selected');
        hideSelected();
      })
      // ----------------------------------------
      $('#select-all', cvg_point_menu).mouseup(function() {
        th.addClass('selected');
      })
      $('#select-others', cvg_point_menu).mouseup(function() {
        th.addClass('selected');
        source.removeClass('selected');
      })
      $('#unselect-all', cvg_point_menu).mouseup(function() {
        th.removeClass('selected');
      })
      $('#invert', cvg_point_menu).mouseup(function() {
        th.toggleClass('selected');
      })
      // ----------------------------------------
      $('#hide-selected', cvg_point_menu).mouseup(function() {
        hideSelected();
      })
      $('#unhide-all', cvg_point_menu).mouseup(function() {
        allVisible();
        resetBuckets();
        self.build();
      })
      // ----------------------------------------
      $('#sort-up', cvg_point_menu).mouseup(function() {
        table.trigger("sorton", [[[source.attr('data-column'), 0]]]);
      })
      $('#sort-down', cvg_point_menu).mouseup(function() {
        table.trigger("sorton", [[[source.attr('data-column'), 1]]]);
      })
      // ----------------------------------------
      $('#hide-hits', cvg_point_menu).mouseup(function() {
        options.hide_hits = $('span.ui-icon', this).toggleClass('check').hasClass('check');
        if (options.hide_hits) {
          $('tr.hit', where).hide();
        } else {
          $('tr.hit', where).show();
        }
      })
      $('#hide-dontcare', cvg_point_menu).mouseup(function() {
        options.hide_dont_care = $('span.ui-icon', this).toggleClass('check').hasClass('check');
        if (options.hide_dont_care) {
          $('tr.dont_care', where).hide();
        } else {
          $('tr.dont_care', where).show();
        }
      })
      $('#hide-illegal', cvg_point_menu).mouseup(function() {
        options.hide_illegal = $('span.ui-icon', this).toggleClass('check').hasClass('check');
        if (options.hide_illegal) {
          $('tr.illegal', where).hide();
        } else {
          $('tr.illegal', where).show();
        }
      })
      $('#hide-both', cvg_point_menu).mouseup(function() {
        var hide_both = $('span.ui-icon', this).toggleClass('check').hasClass('check');
        options.hide_dont_care = hide_both;
        options.hide_illegal   = hide_both;
        if (hide_both) {
          $('tr.illegal, tr.dont_care', where).hide();
          $('#hide-illegal span.ui-icon, #hide-dontcare span.ui-icon', cvg_point_menu).addClass('check');
        } else {
          $('tr.illegal, tr.dont_care', where).show();
          $('#hide-illegal span.ui-icon, #hide-dontcare span.ui-icon', cvg_point_menu).removeClass('check');
        }
      })
      // ----------------------------------------
      if (two_axes()) {
        $('#matrix', cvg_point_menu).mouseup(function() {
          options.matrix = $('span.ui-icon', this).toggleClass('check').hasClass('check')?matrix.matrix:matrix.table;
          self.build();
        })
      }
      if (one_axis()) {
        $('#graph', cvg_point_menu).mouseup(function() {
          options.matrix = $('span.ui-icon', this).toggleClass('check').hasClass('check')?matrix.graph:matrix.table;
          self.build();
        })
      }
      // ----------------------------------------
      if (coverpoint.cumulative === true) {
        $('#heat', cvg_point_menu).mouseup(function() {
          if (coverpoint.hasOwnProperty('heat_map')) {
            $(this).toggleClass('grey');
            options.heat_map = !$(this).hasClass('grey');
            if (options.heat_map && !buckets.hasOwnProperty('heat_map')) {
              // derived axis may not have computed heat map; redo
              updateBuckets();
            }
          } else {
            var url = '/hm/' + log_id + '/' + coverpoint.offset + '/' + coverpoint.buckets.length;
            var span = $('span.ui-icon', this);
            $.getJSON(url, function(data) {
              coverpoint.heat_map = data;
              coverpoint.heat_map.buckets = new Array();
              // populate bucket array with correctly indexed heat buckets
              data.data.forEach(function(bucket){
                coverpoint.heat_map.buckets[bucket[0].bucket_id - coverpoint.offset] = new heat_bkt(bucket);
              });
              // this is where data is used from
              buckets.heat_map = coverpoint.heat_map.buckets;
              span.addClass('check');
              options.heat_map = true;
              if (!all_visible()) {
                // redo the aggregation computation to include heat data
                updateBuckets();
              }
            });
          }
        })
      }
    }

    function build_table() {
      where.append('<div class="table"><table><thead><tr><th class="bkt">bucket</th>' +
        axes.reduce(function(p, c, idx){
          return p+((c.visible===false)?'':('<th class="axis sorter-false" idx="'+idx+'">' + c.name + '</th>'))},
          ''
        ) + '<th>goal</th><th>hits</th></thead><tbody id="cvg-point-body"></tbody></table></div>');

      addMenu();
      var body = $("#cvg-point-body", where);
      for (var bucket=0; bucket<buckets.length; bucket++) {
        var bkt = buckets[bucket];
        var title = offset + bucket;
        if (buckets.hasOwnProperty('aliases')) {
          var aliases = buckets.aliases[bucket];
          if (aliases.length > 10) {
            title = aliases.slice(0,5).join(',') + ',...,' + aliases.slice(-5).join(',');
          } else {
            title = aliases.join(',');
          }
        }
        body.append('<tr class="' + coverageTable.classFromBucket(bkt) + '"><td title="' + title + '">' + bucket + '</td>' + permsFromBucket(axes, bucket) + '<td>' + bkt[0] + '</td><td class="hits" bkt="' + bucket + '">' + bkt[1] + '</td></tr>');
      }
      table = $('table', where).tablesorter();
      if (coverpoint.cumulative === true) {
        $('td.hits', body).bind('mouseenter.coverage', function() {
          showBucket($(this));
 	});
      } else if (!all_visible()) {
        $('td.hits', body).bind('mouseenter.coverage', function() {
          showAliases($(this));
 	});
      }
      if (options.hide_hits) {
        $('tr.hit', where).hide();
      }
      if (options.hide_dont_care) {
        $('tr.dont_care', where).hide();
      }
      if (options.hide_illegal) {
        $('tr.illegal', where).hide();
      }
    }

    function build_graph() {
      // add a graph of hits vs axis
      var axis = visible_axes()[0];
      var id =  $coverage.chart_id();

      $('<div>', {id:id, style:'margin:auto', height:500, width:750}).appendTo(where);
      if (options.heat_map) {
        var tests = coverpoint.heat_map.testnames.sort(function(l,r){return l.hits < r.hits});
        // return list of (hits per test) list
        var data = tests.map(function(test){
          // for each test return list of hits
          return buckets.map(function(bkt, idx) {
            return buckets.heat_map[idx].hits(test.idx);
          });
        });

        $.jqplot(id, data,
          {
          stackSeries: true,
          seriesDefaults: {
            renderer: $.jqplot.BarRenderer,
          },
          axes: {
            xaxis: {
              renderer: $.jqplot.CategoryAxisRenderer,
              ticks: axis.values
            },
            yaxis: {
              min: 0
            }
          }
        });
        var info = $('<div>', {class:'popup'}).appendTo(where);
        function popup(ev, seriesIndex, pointIndex, data) {
          info.show();
          info.html('<p><b>'+tests[seriesIndex].testname+'<b></p><p>value: '+axis.values[pointIndex]+'</p><p><i>'+data[1]+' hits, '+ ((data[1]*parseFloat(100))/buckets[pointIndex][1]).toFixed(2) +'%</i></p>');
        };
        $('#'+id, where).bind('jqplotMouseMove', function(ev, gridpos, datapos, neighbor, plot){
          if (neighbor === null) {
            info.hide();
            return;
          }
          info.offset({ top: ev.pageY - info.height() - 1, left: ev.pageX + 1 });
        });
        $('#'+id, where).bind('jqplotDataMouseOver', popup);
        $('#'+id, where).bind('jqplotMouseLeave', function(){info.hide()});
      } else {
        $.jqplot(id, [buckets.map(function(it, idx){return [axis.values[idx], it[1]]})], {
          axes: {
            xaxis: {
              renderer: $.jqplot.CategoryAxisRenderer
            },
            yaxis: {
              min: 0
            }
          }
        });
      }
      // navigate back
      where.append($('<h5><a>Back to table view</a></h5>').click(function(){options.matrix=matrix.table; self.build()}));

    }

    function build_matrix() {
      var _axes = visible_axes();
      // Use jqote & template in index to create matrix table
      where.jqoteapp('#matrix-template', {
        x_axis : _axes[1],
        y_axis : _axes[0],
        buckets : buckets
      });
      // easiest way to place title in 1st data row
      $('tr:nth(2)', where).prepend($('<th/>', {class : 'title rotated', rowspan : _axes[0].values.length, text : _axes[0].name}))

      var cells = $('th,td', where).not('.title');
      var width = Array.max(cells.map(function(idx,it){return $(it).width()}));
      cells.css('height', width).css('width', width);
      $('td.hits', where).bind('mouseenter.coverage', function() {
        if (coverpoint.cumulative === true) {
          showBucket($(this));
        } else {
          showAliases($(this));
        }
      });
      if (coverpoint.cumulative === true) {
        if (options.heat_map) {
          var tests = coverpoint.heat_map.testnames.sort(function(l,r){return l.hits < r.hits});
          var cells = $('td[bkt]', where);
          var container = $('<table class="heat-map"><tbody><tr><td rowspan=99>Heat Map</td></tr></tbody></table>');
          $('div.table', where).append(container);
          [
            {name:'%total', description : 'total', metric : function(cell, test, bkt) {
              var hits = buckets.heat_map[bkt].hits(test.idx);
              cell.text(hits);
              return hits/parseFloat(buckets[bkt][1]);
            }},
            {name:'%max', description : 'max', metric : function(cell, test, bkt, max) {
              var hits = buckets.heat_map[bkt].hits(test.idx);
              cell.text(hits);
              return hits/max;
            }}
          ].forEach(function(metric, midx) {
            var sel = $('tr:nth('+midx+')', container);
            if (sel.length < 1) {
              sel = $('<tr/>').appendTo($('tbody', container));
            }
            tests.forEach(function(test, idx){
              var color = $.jqplot.config.defaultColors[idx], r = parseInt(color.slice(1,3), 16), g = parseInt(color.slice(3, 5), 16), b = parseInt(color.slice(5, 7), 16);
              var cell = $('<td>', {title:test.testname}).css({'background-color': color, width:40, height:40}).appendTo(sel);
              var max = parseFloat(Math.max.apply(null, buckets.heat_map.map(function(it) { // the maximum is constant of bkt
                return it.hits(test.idx);
              })));
              cell.tooltip({position:{at:'middle bottom-15px', my:'middle bottom-15px'}, track:true});
              cell.bind('mouseenter.example', function() {
                // colour cells with hits
                cells.each(function(id, it) {
                  var bkt = $(this).attr('bkt');
                  $(this).css('background-color', 'rgba('+r+','+g+','+b+','+metric.metric($('div#hits', this), test, bkt, max)+')');
                });
              });
            });
            $('<td>', {text: metric.name, title: metric.description}).tooltip().appendTo(sel);
          });
          container.bind('mouseleave.example', function() {
            // remove colouring
            cells.css('background-color', '');
            cells.each(function(idx, it) {
              $('div#hits', this).text(buckets[$(this).attr('bkt')][1]);
            });
          });
        }
      }
      // navigate back
      $('div.table', where).append($('<h5><a>Back to table view</a></h5>').click(function(){options.matrix=matrix.table; self.build()}));
    }

    this.coverage = function() {
      var coverage = buckets.reduce(function(sum, it){if (it[0] > 0) {sum.goal += it[0]; sum.hits += Array.min(it.slice(0,2))}; return sum;}, {goal : 0, hits : 0});
      if (coverage.goal < 0) {
        coverage.status = 'error';
        coverage.coverage = -1;
      } else {
        coverage.coverage = (100.0 * coverage.hits)/coverage.goal;
        if (coverage.goal == coverage.hits) {
          coverage.status = 'hit';
        } else if (coverage.hits > 0) {
          coverage.status = 'some';
        } else {
          coverage.status = 'unhit';
        }
      }
      coverage.description = coverage.hits + ' of ' + coverage.goal + ' is ' + coverage.coverage.toFixed(2);
      return coverage;
    }

    this.build = function() {
      where.html($('<h3/>', {html: title}));
      setTimeout(function() {
        if (options.matrix == matrix.matrix) {
          build_matrix();
        } else if (options.matrix == matrix.graph) {
          build_graph();
        } else {
          build_table();
        }
        var table = $('div.table', where);
        if (table.length) $report.fit(table);
      }, 0);
    }

    // on construction
    if (options.hasOwnProperty('axis')) {
      axes.map(function(it){it.visible = it.name == options.axis});
      updateBuckets();
    }

    // on construction
    if (options.build !== false) {
      this.build();
    }
    options.build = true;

    console.log(this);
  };

  $coverage.coverageTable.classFromBucket = function classFromBucket(bucket) {
    switch (bucket[0]) {
    case  0 :
      return 'dont_care';
    case -1 :
	if (bucket[1] > 0) return 'illegal hit';
      return 'illegal';
    default :
      if (bucket[1] >= bucket[0]) return 'hit';
      if (bucket[1] >  0) return 'some';
      return 'unhit';
    }
  }

  $coverage.coverageTable.RGBFromCoverage = function RGBFromCoverage(coverage) {
    // start at red, fade to yellow then to green
    if (Math.floor(coverage) == 100) {
      return '#cfc';
    }
    var lo, hi, mix;
    lo = [255, 160 , 160];
    hi = [255, 255, 192];
    mix = coverage;
    mix /= parseFloat(100);
    var result = lo.map(function(it, idx) {
      var val = lo[idx]*(1-mix) + hi[idx]*mix;
      if (val < 0) val = 0;
      if (val > 255) val = 255;
      return val.toFixed();
    });
    return 'rgb(' + result.join(', ') + ')';
  }

  $coverage.coverage = function(pane, log_id, data) {
    var self = this;
    var cvg_point_pane = $('<div class="cvg-point-pane"></div>').appendTo(pane);
    var cvg_tree_pane  = $('<div class="cvg-tree-pane"></div>' ).appendTo(pane);

    function formatCoverage(coverage) {
      return '<i class="' + coverage.status + '" coverage="' + coverage.coverage.toFixed(2) + '">' + coverage.description + '</i>';
    }

    function generateCoverpointHierarchy(coverpoint) {
      coverpoint = coverpoint || data;
      var node = {key : coverpoint.id, expand : false, unselectable: true};
      var title;
      if (coverpoint.hierarchy) {
        title = coverpoint.hierarchy;
    	if (coverpoint.children.some(function(it){return it.hierarchy;})) {
          node.isFolder = true;
   	}
        if (coverpoint.children) {
      	  node.children = coverpoint.children.map(function(child){return generateCoverpointHierarchy(child);});
        }
      } else {
        title = coverpoint.coverpoint;
        node.isFolder = true;
        node.children = coverpoint.axes.map(function(axis){return {title:'<em style="white-space:pre">' + axis.name + ' </em>', key : axis.name, expand : false, unselectable: true}});
      }
      node.title = '<b>' + title + '</b><em style="white-space:pre"> ' + coverpoint.description + ' </em>'
      if (coverpoint.coverage) {
        node.title += formatCoverage(coverpoint.coverage);
      }
      return node;
    }

    function findCoverpointData(id, coverpoint) {
      coverpoint = coverpoint || data;
      if (coverpoint.id == id) {
        return coverpoint;
      }
      for (child in coverpoint.children) {
        var found = findCoverpointData(id, coverpoint.children[child]);
        if (found) {
          return found;
        }
      }
      return false;
    }

    function getCoverpointName(id, coverpoint) {
      coverpoint = coverpoint || data;
      if (coverpoint.id == id) {
        return '<a class="hierarchy" title="'+coverpoint.description+'">'+coverpoint.coverpoint+'</a>';
      }
      for (child in coverpoint.children) {
        var found = getCoverpointName(id, coverpoint.children[child]);
        if (found) {
          return '<a class="hierarchy" title="'+coverpoint.description+'">'+coverpoint.hierarchy+'</a> >> ' + found;
        }
      }
      return false;
    }

    this.tree = cvg_tree_pane.dynatree({
      children : [generateCoverpointHierarchy(),],
      onClick: function(node, event) {
        function expand() {
          node.parent.childList.forEach(function(sibling) {sibling.expand(node == sibling)});
        }
        if (node.hasOwnProperty('coverageTable')) {
          if (node.bExpanded) {
            node.expand(false);
          } else {
            node.coverageTable.build();
            expand();
          }
          return false;
        }
        var cData = findCoverpointData(node.data.key);
        if (cData == false) return true;
        var title = getCoverpointName(node.data.key);
        if (cData.hasOwnProperty('coverpoint')) {
          node.coverageTable = new $coverage.coverageTable(log_id, cvg_point_pane, title, cData);
          expand();
          node.childList.forEach(function(axis){
            axis.coverageTable = new $coverage.coverageTable(log_id, cvg_point_pane, title + ' : ' + axis.data.key, cData, {build : false, axis : axis.data.key, lock : true});
            axis.data.title += ' ' + formatCoverage(axis.coverageTable.coverage());
            axis.render();
          });
        } else {
          node.expand(!node.bExpanded);
          if (node.bExpanded && cData !== false && cData.hasOwnProperty('hierarchy')) {
            node.coverageTable = new $coverage.coverageSummaryTable(self.tree, cvg_point_pane, title, cData);
          }
        }
        return false;
     },
     onCreate : function(node, nodeSpan) {
       setTimeout(function() {
         $('i', nodeSpan).each(function() {
           var i = $(this),
               height = $(nodeSpan).height(),
               width = 100,
               cvg = i.attr('coverage'),
               coverage = parseFloat(cvg),
               canvas = $('<canvas>', {style:'z-index:1; position:relative; float:right', height:height, width:width, title:cvg+'%'}).insertBefore(nodeSpan),
               color = $coverage.coverageTable.RGBFromCoverage(coverage);
           $(nodeSpan).css('position', 'relative').css('width', '100%');
           canvas[0].width = width;
           canvas[0].height = height;
           var ctx = canvas[0].getContext('2d');
           ctx.fillStyle = color;
           ctx.fillRect(0, 0, width, height);
           var clr = (width-1)*coverage/100;
           ctx.clearRect(1+clr, 1, width-clr-1, height-2);
           ctx.fillRect(width-1, 0, width-1, height); // fill that pesky end bit in
           canvas.tooltip({content:'<a style="background-color:'+color+'">'+cvg+'%</a>', tooltipClass: "cvg-tooltip",});
         })
       }, 0);
     }
    });

    // add scrollbar if necessary
    $report.fit(cvg_tree_pane, false);
  };

})($coverage);
  
