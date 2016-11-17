// Generated by CoffeeScript 1.9.2
(function() {
  $(document).ready(function() {
    var mapContainer, mapId;
    jQuery.cScript = function(url, options) {
      options = $.extend(options || {}, {
        dataType: 'script',
        cache: true,
        url: url
      });
      return jQuery.ajax(options);
    };
    mapId = 'leaflet-map';
    mapContainer = $("#" + mapId);
    $.fn.placeMap = function(options) {
      var defaults, element, layers, onSelect;
      element = $(this).hide();
      if (element.data('selecturl') !== void 0) {
        element.select2('destroy');
      }
      layers = {};
      defaults = {
        mapContainer: void 0,
        height: '200px',
        initial: {
          lat: -8.557,
          lng: 125.575
        },
        zoom: 14,
        mapContainerID: 'myMap',
        onSelect: function(feature) {
          var o;
          if (element.prop('tagName') === 'SELECT') {
            if (!element.attr('multiple')) {
              element.children('option').remove();
            }
            o = "<option selected=selected value='" + feature.properties.pcode + "'>" + feature.properties.name + "</option>";
            element.append($(o));
          }
          if (element.prop('tagName') === 'SELECT') {
            return element.val(feature.properties.pcode);
          }
        }
      };
      options = $.extend(options, defaults);
      onSelect = options.onSelect;
      if (options.mapContainer === void 0) {
        mapContainer = $('<div>').attr('id', options.mapContainerID).css({
          width: $(this).parents('.form-group:first').css('width'),
          height: options.height
        }).insertAfter($(this));
      }
      if (typeof $.fn.waiting === 'function') {
        mapContainer.waiting();
        mapContainer.waiting('play');
      }
      return $.cScript('/static/leaflet/leaflet.js').done(function() {
        var addJSONLayer, addUTFLayer, marker;
        marker = L.marker;
        if (typeof $.fn.waiting === 'function') {
          mapContainer.waiting('destroy');
        }
        window.Lmap = L.map(options.mapContainerID);
        Lmap.setView(options.initial, options.zoom);
        L.tileLayer('/tileserver/testing/{z}/{x}/{y}.png', {
          attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>',
          maxZoom: 18
        }).addTo(Lmap);
        addUTFLayer = function(Lmap, options) {
          defaults = {
            blockClass: 'btn btn-primary btn-block btn-xs'
          };
          options = $.extend(defaults, options);
          return $.cScript('/static/leaflet/leaflet.utfgrid.js').done(function() {
            var hoveringOver, icon, info, invisibleicon, utfGrid;
            icon = L.icon({
              iconUrl: '/static/leaflet/images/marker-icon.png'
            });
            invisibleicon = L.icon({
              iconUrl: '/static/leaflet/images/invisible.png'
            });
            utfGrid = new L.UtfGrid('/tileserver/utfgrid/{z}/{x}/{y}.json?callback={cb}', {
              resolution: 4
            });
            Lmap.addLayer(utfGrid);
            info = L.control({
              position: 'bottomleft'
            });
            hoveringOver = 10101;
            utfGrid.on('click', function(e) {
              var content;
              content = '';
              if (e.data !== null) {
                console.log(e.data);
                marker = L.marker(e.latlng, {
                  icon: invisibleicon
                });
                content += "<div style='width: 150px;'>";
                content += "<button class='" + options.blockClass + "' data-addpcode='" + (parseInt(e.data.pcode / 100 / 100)) + "'>Add Munisipio " + e.data.district + "</button>";
                content += "<button class='" + options.blockClass + "' data-addpcode='" + (parseInt(e.data.pcode / 100)) + "'>Add Postu Admin. " + e.data.sd + "</button>";
                content += "<button class='" + options.blockClass + "' data-addpcode='" + (parseInt(e.data.pcode)) + "'>Add Suku " + e.data.suco + "</button>";
                content += '</div>';
                marker.bindPopup(content).addTo(Lmap).openPopup();
              }
            });
            info.onAdd = function(map) {
              var el, header, hovering;
              el = void 0;
              header = void 0;
              hovering = void 0;
              this._div = L.DomUtil.create('div', 'info');
              el = $(this._div);
              header = $('<h4>').text('Hovering over');
              hovering = $('<b class="hovering-over"></b>').text('Nothing yet');
              el.append(header);
              el.append(hovering);
              return this._div;
            };
            info.update = function(props) {
              var header, place;
              header = void 0;
              header = $('<h4>').text('Hovering over');
              if (props) {
                hoveringOver = props.data;
                place = props.data.suco + '/ ' + props.data.sd + '/ ' + props.data.district;
                if ($(this._div).find('.hovering-over').text() !== place) {
                  $(this._div).find('.hovering-over').text(props.data.suco + ', ' + props.data.sd + ', ' + props.data.district);
                }
              }
            };
            info.addTo(Lmap);
            utfGrid.on('mouseover', function(e) {
              if (e.data) {
                info.update(e);
              }
            });
            return addJSONLayer(Lmap);
          });
        };
        addJSONLayer = function(Lmap, options) {
          defaults = {
            singleArea: true,
            url: '/geo/places.json?pcode=0',
            json_url: '/geo/places.json?pcode=',
            onEachFeature: function(feature, layer) {
              var popupContent;
              console.log(layer);
              popupContent = "<button class='btn btn-warning btn-block' data-removepcode=" + feature.properties.pcode + ">Remove " + feature.properties.name + "</button>";
              if (feature.properties && feature.properties.popupContent) {
                popupContent += feature.properties.popupContent;
              }
              layer.bindPopup(popupContent);
              return onSelect(feature);
            }
          };
          options = $.extend(options, defaults);
          return $.cScript('/static/leaflet/leaflet.ajax.min.js').done(function() {
            var geojsonLayer;
            geojsonLayer = new L.GeoJSON.AJAX(options.url, {
              onEachFeature: options.onEachFeature
            });
            geojsonLayer.addTo(Lmap);
            $(document).on('click', '[data-addpcode]', function(e) {
              var pcode;
              e.preventDefault();
              pcode = $(this).data('addpcode');
              if (layers[pcode] !== void 0) {
                console.warn('Already present: not adding');
                console.log(layers[pcode]);
                return;
              }
              if (defaults.singleArea) {
                layers = {};
                geojsonLayer.clearLayers();
              }
              $.getJSON(options.json_url + pcode, function(data) {
                var addedLayer;
                addedLayer = L.geoJson(data, {
                  onEachFeature: options.onEachFeature
                });
                geojsonLayer.addLayer(addedLayer);
                return layers[pcode] = addedLayer;
              });
              if (marker !== void 0) {
                Lmap.removeLayer(marker);
              }
              return false;
            });
            return $(document).on('click', '[data-removepcode]', function() {
              Lmap.removeLayer(layers[$(this).data('removepcode')]);
              return layers[$(this).data('removepcode')] = void 0;
            });
          });
        };
        return addUTFLayer(Lmap);
      });
    };
    return $.fn.modalPlaceMap = function(options) {
      var defaults;
      defaults = {
        selector: '[name=place]',
        other: void 0
      };
      options = $.extend(options, defaults);
      return $(this).find(options.selector).placeMap();
    };
  });

}).call(this);
