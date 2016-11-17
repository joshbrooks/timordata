$(document).ready ->

  # Cached Script loader
  jQuery.cScript = (url, options) ->
    options = $.extend(options or {},
      dataType: 'script'
      cache: true
      url: url)
    jQuery.ajax options
  mapId = 'leaflet-map'
  mapContainer = $("#"+mapId)

  $.fn.placeMap = (options) ->

    element = $(this).hide()
    if element.data('selecturl') isnt undefined
      element.select2('destroy')

    layers = {}
    defaults =
      mapContainer: undefined
      height: '200px'
      initial :
        lat: -8.557
        lng: 125.575
      zoom : 14
      mapContainerID: 'myMap'
      onSelect: (feature)->
        if element.prop('tagName') is 'SELECT'
          if not element.attr('multiple')
            element.children('option').remove()
          o = "<option selected=selected value='#{feature.properties.pcode}'>#{feature.properties.name}</option>"
          element.append($(o))

        if element.prop('tagName') is 'SELECT'
          element.val(feature.properties.pcode)

    options = $.extend(options, defaults)
    onSelect = options.onSelect

    # Append a place map underneath a "place" field on a form
    if options.mapContainer is undefined
      mapContainer = $('<div>')
        .attr('id', options.mapContainerID)
        .css
          width: $(this).parents('.form-group:first').css('width')
          height: options.height
        .insertAfter($(this))

    if (typeof($.fn.waiting) == 'function')
      mapContainer.waiting()
      mapContainer.waiting('play')

    $.cScript('/static/leaflet/leaflet.js').done ->
      marker = L.marker
      if (typeof($.fn.waiting) == 'function')
        mapContainer.waiting('destroy')
      window.Lmap = L.map(options.mapContainerID)
      Lmap.setView(options.initial, options.zoom)
      L.tileLayer('/tileserver/testing/{z}/{x}/{y}.png',
        attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>'
        maxZoom: 18).addTo Lmap

      addUTFLayer = (Lmap, options) ->

        defaults =
          blockClass: 'btn btn-primary btn-block btn-xs'

        options = $.extend(defaults, options)

        $.cScript('/static/leaflet/leaflet.utfgrid.js').done ->
          icon = L.icon(iconUrl: '/static/leaflet/images/marker-icon.png')
          invisibleicon = L.icon(iconUrl: '/static/leaflet/images/invisible.png')

          utfGrid = new (L.UtfGrid)('/tileserver/utfgrid/{z}/{x}/{y}.json?callback={cb}', resolution: 4)
          Lmap.addLayer utfGrid
          info = L.control(position: 'bottomleft')
          hoveringOver = 10101
          utfGrid.on 'click', (e) ->
            content = ''
    #        if marker != undefined
    #          console.log 'Lmap.removeLayer marker'
    #          Lmap.removeLayer marker
    #          console.log 'Lmap.removeLayer marker done'
            # Prevent error in the console if click is on a location without data (ocean areas / overseas)
            if e.data isnt null
              console.log e.data
              marker = L.marker(e.latlng , icon: invisibleicon)

              content += "<div style='width: 150px;'>";
              content += "<button class='#{options.blockClass}' data-addpcode='#{parseInt(e.data.pcode / 100 / 100)}'>Add Munisipio #{e.data.district}</button>"
              content += "<button class='#{options.blockClass}' data-addpcode='#{parseInt(e.data.pcode / 100 )}'>Add Postu Admin. #{e.data.sd}</button>"
              content += "<button class='#{options.blockClass}' data-addpcode='#{parseInt(e.data.pcode )}'>Add Suku #{e.data.suco}</button>"
              contetn += '</div>';

              marker.bindPopup(content).addTo(Lmap).openPopup()
              return

          info.onAdd = (map) ->
            el = undefined
            header = undefined
            hovering = undefined
            @_div = L.DomUtil.create('div', 'info')
            el = $(@_div)
            header = $('<h4>').text('Hovering over')
            hovering = $('<b class="hovering-over"></b>').text('Nothing yet')
            el.append header
            el.append hovering
            @_div

          info.update = (props) ->
            header = undefined
            header = $('<h4>').text('Hovering over')
            if props
              hoveringOver = props.data
              place = props.data.suco + '/ ' + props.data.sd + '/ ' + props.data.district
              if $(@_div).find('.hovering-over').text() != place
                $(@_div).find('.hovering-over').text props.data.suco + ', ' + props.data.sd + ', ' + props.data.district
            return

          info.addTo Lmap
          utfGrid.on 'mouseover', (e) ->
            if e.data
              info.update e
            return
          addJSONLayer Lmap

      addJSONLayer = (Lmap, options) ->
        defaults =
          singleArea: true
          url: '/geo/places.json?pcode=0' # Dummy URL to get a JSON layer
          json_url: '/geo/places.json?pcode='
          onEachFeature : (feature, layer) ->
            console.log layer
            popupContent = "<button class='btn btn-warning btn-block' data-removepcode=#{feature.properties.pcode}>Remove #{feature.properties.name}</button>"
            if feature.properties and feature.properties.popupContent
              popupContent += feature.properties.popupContent
            layer.bindPopup popupContent
            onSelect(feature)

        options = $.extend(options, defaults)


        $.cScript('/static/leaflet/leaflet.ajax.min.js').done ->
          geojsonLayer= new (L.GeoJSON.AJAX)(options.url, onEachFeature: options.onEachFeature)
          geojsonLayer.addTo Lmap

          $(document).on 'click', '[data-addpcode]', (e) ->
            e.preventDefault()
            pcode = $(this).data('addpcode')
            if layers[pcode] isnt undefined
              console.warn 'Already present: not adding'
              console.log layers[pcode]
              return
            if defaults.singleArea
              layers = {}
              geojsonLayer.clearLayers()

            $.getJSON options.json_url + pcode, (data) ->
              addedLayer = L.geoJson(data, onEachFeature: options.onEachFeature)
              geojsonLayer.addLayer addedLayer
              layers[pcode] = addedLayer

            if marker isnt undefined
              Lmap.removeLayer marker
            return false

          $(document).on 'click', '[data-removepcode]', () ->
            Lmap.removeLayer(layers[($(this).data('removepcode'))])
            layers[($(this).data('removepcode'))] = undefined

      addUTFLayer Lmap

  $.fn.modalPlaceMap = (options) ->

    defaults =
      selector: '[name=place]'
      other: undefined

    options = $.extend(options, defaults)
    # Call this on a Modal to trigger a leaflet place map for any "place" input
    $(this).find(options.selector).placeMap()
