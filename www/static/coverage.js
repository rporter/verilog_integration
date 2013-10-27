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

$coverage = function(){};

(function($coverage) {

  $coverage.coverageTable = function coverageTable(log_id, where, name, coverpoint, options) {
    var self    = this;
    var buckets = coverpoint.buckets;
    var axes    = $.extend(true, [], coverpoint.axes);
    var offset  = coverpoint.offset;
    var table;
    options = options || {hide_hits : false, hide_illegal : false, hide_dont_care : false, matrix : false};

    function visible_axes() {
      return axes.reduce(function(sum, it, idx){
        if (it.visible !== false) {
          sum.push(it);
        }
        return sum;
      }, Array());
    }
    function two_axes() {
      return visible_axes().length == 2;
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

    function showBucket(node) {
      var bucket_id = parseInt(node.attr('bkt'));
      var bucket    = buckets[bucket_id];
      var url       = '/bkt/' + log_id + '/';
console.log(bucket);
      if (bucket.length < 3) {
        url += (bucket_id + offset);
      } else {
        url += bucket[2].map(function(bkt){return bkt+offset}).join(',');
      }
      node.html(function(){
        return '<a class="popup">' + $(this).text() + '<span id="hits-' + bucket_id + '" title="hit details for ' + log_id + '/' + bucket_id + '"></span></a>';
      });
      $.getJSON(url, function(data) {
        $('span', node).html(function() {
          if (data.length) {
            return $('<table/>', {
              class : 'bucket',
              html : '<tbody>'+data.slice(0,10).map(function(it){
                return '<tr class="'+coverageTable.classFromBucket([bucket[0], it.hits])+'"><td>'+it.log_id+'</td><td>'+it.hits+'</td></tr>';
              })+'</tbody>'
            });
          } else {
            return $('<i/>', {html : 'no hits'});
          }
  	});
      });
      node.unbind('mouseenter.coverage'); // don't do again
      node.bind('click.coverage', function(){
        $('span', node).clone().dialog();
      });
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

    function updateBuckets() {
      if (!checkBuckets()) {
        return false;
      }
      // reduce buckets
      buckets = [];
      for (var bucket=0; bucket<coverpoint.buckets.length; bucket++) {
        var idx = bucketIdx(axisIdxs(bucket));
        if (buckets[idx] === undefined) {
          buckets[idx] = coverpoint.buckets[bucket].concat([[bucket,]]);
        } else {
          if (coverpoint.buckets[bucket][0] > 0) {
            if (buckets[idx][0] < 0) {
              // previously marked as illegal
              buckets[idx][0] = coverpoint.buckets[bucket][0];
            } else {
              buckets[idx][0] += coverpoint.buckets[bucket][0];
            }
          }
          buckets[idx][1] += coverpoint.buckets[bucket][1];
          buckets[idx][2].push(bucket)
        }
      }
      return true;
    }

    function resetBuckets() {
      buckets = coverpoint.buckets;
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
        if (options.matrix) {
          $('#matrix span.ui-icon', cvg_point_menu).addClass('check');
        }
      } else {
        options.matrix = false;
        $('#matrix', cvg_point_menu).addClass('grey');
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
      $('#matrix', cvg_point_menu).mouseup(function() {
        if (!two_axes()) return true;
        options.matrix = $('span.ui-icon', this).toggleClass('check').hasClass('check');
        self.build();
      })
    }

    function build_table() {
      where.append('<div class="t"><table><thead><tr><th class="bkt">bucket</th>' +
        axes.reduce(function(p, c, idx){
          return p+((c.visible===false)?'':('<th class="axis sorter-false" idx="'+idx+'">' + c.name + '</th>'))},
          ''
        ) + '<th>goal</th><th>hits</th></thead><tbody id="cvg-point-body"></tbody></table></div>');

      addMenu();
      var body = $("#cvg-point-body", where);
      for (var bucket=0; bucket<buckets.length; bucket++) {
        var bkt = buckets[bucket];
        var title = offset + bucket;
        if (bkt.length > 2) {
          if (bkt[2].length > 10) {
            title = bkt[2].slice(0,5).join(',') + ',...,' + bkt[2].slice(-5).join(',');
          } else {
            title = bkt[2].join(',');
          }
        }
        body.append('<tr class="' + coverageTable.classFromBucket(bkt) + '"><td title="' + title + '">' + bucket + '</td>' + permsFromBucket(axes, bucket) + '<td>' + bkt[0] + '</td><td class="hits" bkt="' + bucket + '">' + bkt[1] + '</td></tr>');
      }
      table = $('table', where).tablesorter();
      if (coverpoint.cumulative === true) {
        $('td.hits', body).bind('mouseenter.coverage', function() {
          showBucket($(this));
 	});
      }
      if (options.hide_dont_care) {
        $('tr.dont_care', where).hide();
      }
      if (options.hide_illegal) {
        $('tr.illegal', where).hide();
      }
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
      // navigate back
      $('div.t', where).append($('<h5><a>Back to table view</a></h5>').click(function(){options.matrix=false; self.build()}));

      var cells = $('th,td', where).not('.title');
      var width = Array.max(cells.map(function(idx,it){return $(it).width()}));
      cells.css('height', width).css('width', width);
      if (coverpoint.cumulative === true) {
        $('td.hits', where).bind('mouseenter.coverage', function() {
          showBucket($(this));
 	});
      }
    }

    this.build = function() {
      where.html($('<h3/>', {html: name}));
      if (options.matrix) {
        build_matrix(where);
      } else {
        build_table(where);
      }
    }

    // on construction
    this.build();

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

  $coverage.coverage = function(pane, log_id, data) {
    var self = this;
    var cvg_point_pane = $('<div class="cvg-point-pane"></div>').appendTo(pane);
    var cvg_tree_pane  = $('<div class="cvg-tree-pane"></div>' ).appendTo(pane);

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
      }
      node.title = '<b>' + title + '</b> ' + coverpoint.description + ' '
      if (coverpoint.coverage) {
        node.title += '<i class="' + coverpoint.coverage.status + '">' + coverpoint.coverage.description + '</i>'
      }
      return node;
    }

    function findCoverpointJSON(id, coverpoint) {
      coverpoint = coverpoint || data;
      if (coverpoint.id == id) {
        return coverpoint;
      }
      for (child in coverpoint.children) {
        var found = findCoverpointJSON(id, coverpoint.children[child]);
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
        var json = findCoverpointJSON(node.data.key);
        if (json !== false && json.hasOwnProperty('coverpoint')) {
          this.coverageTable = new $coverage.coverageTable(log_id, cvg_point_pane, getCoverpointName(node.data.key), json);
        } else {
          node.expand(!node.bExpanded);
        }
        return false;
     }
    });
  };

})($coverage);
  
